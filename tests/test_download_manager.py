"""DownloadManager tests using a fake engine (no yt-dlp, no network)."""

import threading
import time
from pathlib import Path

from video_downloader.core.errors import DownloadCancelled, DownloadFailedError
from video_downloader.core.event_bus import EventBus
from video_downloader.models.download import (
    DownloadMode,
    DownloadRequest,
    DownloadState,
    DownloadTask,
)
from video_downloader.services.download_manager import DownloadManager


def make_request(url: str = "https://example.com/v") -> DownloadRequest:
    return DownloadRequest(
        url=url, title="t", mode=DownloadMode.VIDEO_AUDIO, output_dir=Path("/tmp")
    )


class FakeEngine:
    """Configurable stand-in for YtdlpService."""

    def __init__(self, duration: float = 0.05, fail: bool = False):
        self.duration = duration
        self.fail = fail
        self.started = threading.Event()
        self.concurrent = 0
        self.max_concurrent_seen = 0
        self._lock = threading.Lock()

    def download(self, task: DownloadTask, bus: EventBus) -> Path:
        with self._lock:
            self.concurrent += 1
            self.max_concurrent_seen = max(self.max_concurrent_seen, self.concurrent)
        self.started.set()
        try:
            deadline = time.monotonic() + self.duration
            while time.monotonic() < deadline:
                if task.cancel_event.is_set():
                    raise DownloadCancelled()
                time.sleep(0.005)
            if self.fail:
                raise DownloadFailedError("boom", detail="boom")
            return Path(f"/tmp/{task.id}.mp4")
        finally:
            with self._lock:
                self.concurrent -= 1

    @staticmethod
    def cleanup_partials(output_dir: Path, media_id: str) -> None:
        pass


def wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_download_completes():
    manager = DownloadManager(FakeEngine(), EventBus(), max_concurrent=1)
    task = manager.enqueue(make_request())
    assert wait_for(lambda: task.state is DownloadState.COMPLETED)
    assert task.output_path == Path(f"/tmp/{task.id}.mp4")
    manager.shutdown()


def test_download_failure_maps_error():
    manager = DownloadManager(FakeEngine(fail=True), EventBus(), max_concurrent=1)
    task = manager.enqueue(make_request())
    assert wait_for(lambda: task.state is DownloadState.ERROR)
    assert task.error == "error_download_failed"
    manager.shutdown()


def test_concurrency_cap_respected():
    engine = FakeEngine(duration=0.2)
    manager = DownloadManager(engine, EventBus(), max_concurrent=2)
    tasks = [manager.enqueue(make_request(f"https://example.com/{i}")) for i in range(5)]
    assert wait_for(lambda: all(t.state is DownloadState.COMPLETED for t in tasks), timeout=10)
    assert engine.max_concurrent_seen <= 2
    manager.shutdown()


def test_cancel_pending_task():
    engine = FakeEngine(duration=0.5)
    manager = DownloadManager(engine, EventBus(), max_concurrent=1)
    first = manager.enqueue(make_request("https://example.com/1"))
    second = manager.enqueue(make_request("https://example.com/2"))
    engine.started.wait(timeout=5)
    manager.cancel(second.id)
    assert second.state is DownloadState.CANCELLED
    assert wait_for(lambda: first.state is DownloadState.COMPLETED, timeout=10)
    manager.shutdown()


def test_cancel_running_task():
    engine = FakeEngine(duration=5.0)
    manager = DownloadManager(engine, EventBus(), max_concurrent=1)
    task = manager.enqueue(make_request())
    engine.started.wait(timeout=5)
    manager.cancel(task.id)
    assert wait_for(lambda: task.state is DownloadState.CANCELLED)
    manager.shutdown()


class FlakyEngine(FakeEngine):
    """Fails the first download, succeeds afterwards."""

    def __init__(self):
        super().__init__(duration=0.05)
        self.calls = 0

    def download(self, task: DownloadTask, bus: EventBus) -> Path:
        self.calls += 1
        self.fail = self.calls == 1
        return super().download(task, bus)


def test_retry_reuses_same_task():
    manager = DownloadManager(FlakyEngine(), EventBus(), max_concurrent=1)
    task = manager.enqueue(make_request())
    assert wait_for(lambda: task.state is DownloadState.ERROR)
    assert task.error == "error_download_failed"

    retried = manager.retry(task.id)
    assert retried is task  # same task, same tile, same history row
    assert wait_for(lambda: task.state is DownloadState.COMPLETED)
    assert task.error is None
    assert task.output_path is not None
    assert len(manager.tasks()) == 1  # no duplicate task was created
    manager.shutdown()


def test_retry_completed_task_is_rejected():
    manager = DownloadManager(FakeEngine(), EventBus(), max_concurrent=1)
    task = manager.enqueue(make_request())
    assert wait_for(lambda: task.state is DownloadState.COMPLETED)
    assert manager.retry(task.id) is None
    manager.shutdown()


def test_retry_after_cancel_pending_runs_exactly_once():
    engine = FakeEngine(duration=0.3)
    manager = DownloadManager(engine, EventBus(), max_concurrent=1)
    first = manager.enqueue(make_request("https://example.com/1"))
    second = manager.enqueue(make_request("https://example.com/2"))
    engine.started.wait(timeout=5)
    manager.cancel(second.id)  # stale queue entry remains for `second`
    assert second.state is DownloadState.CANCELLED

    retried = manager.retry(second.id)  # adds a second queue entry
    assert retried is second
    assert wait_for(lambda: second.state is DownloadState.COMPLETED, timeout=10)
    assert wait_for(lambda: first.state is DownloadState.COMPLETED, timeout=10)
    # the claim guard must prevent the stale entry from re-running the task
    assert engine.max_concurrent_seen <= 1
    manager.shutdown()


def test_clear_finished():
    manager = DownloadManager(FakeEngine(), EventBus(), max_concurrent=1)
    task = manager.enqueue(make_request())
    assert wait_for(lambda: task.state is DownloadState.COMPLETED)
    manager.clear_finished()
    assert manager.tasks() == []
    manager.shutdown()
