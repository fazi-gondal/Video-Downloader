"""History persistence tests."""

from datetime import datetime
from pathlib import Path

from video_downloader.models.download import (
    DownloadMode,
    DownloadRequest,
    DownloadState,
    DownloadTask,
)
from video_downloader.services.history_service import HistoryService


def make_task(state: DownloadState = DownloadState.COMPLETED) -> DownloadTask:
    task = DownloadTask(
        request=DownloadRequest(
            url="https://example.com/v",
            title="Video de prueba",
            mode=DownloadMode.VIDEO_AUDIO,
            output_dir=Path("/tmp"),
        )
    )
    task.state = state
    task.finished_at = datetime.now()
    if state is DownloadState.COMPLETED:
        task.output_path = Path("/tmp/video.mp4")
    return task


def test_record_and_list(tmp_path: Path):
    service = HistoryService(tmp_path / "history.db")
    task = make_task()
    service.record(task)

    entries = service.list_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry.id == task.id
    assert entry.title == "Video de prueba"
    assert entry.state == "completed"
    assert entry.output_path == str(Path("/tmp/video.mp4"))


def test_record_upsert(tmp_path: Path):
    service = HistoryService(tmp_path / "history.db")
    task = make_task(DownloadState.ERROR)
    task.error = "error_download_failed"
    task.output_path = None
    service.record(task)

    task.state = DownloadState.COMPLETED
    task.error = None
    task.output_path = Path("/tmp/ok.mp4")
    service.record(task)

    entries = service.list_entries()
    assert len(entries) == 1
    assert entries[0].state == "completed"
    assert entries[0].output_path == str(Path("/tmp/ok.mp4"))


def test_delete_and_clear(tmp_path: Path):
    service = HistoryService(tmp_path / "history.db")
    first, second = make_task(), make_task()
    service.record(first)
    service.record(second)
    service.delete(first.id)
    assert {e.id for e in service.list_entries()} == {second.id}
    service.clear()
    assert service.list_entries() == []


def test_survives_reopen(tmp_path: Path):
    db = tmp_path / "history.db"
    HistoryService(db).record(make_task())
    assert len(HistoryService(db).list_entries()) == 1
