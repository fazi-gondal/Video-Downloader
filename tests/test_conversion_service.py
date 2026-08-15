"""ConversionService queue tests with a mocked FFmpegService."""

import threading
import time
from pathlib import Path
from unittest import mock

from video_downloader.core.errors import ConversionError
from video_downloader.core.event_bus import EventBus
from video_downloader.core.events import ConversionFinished
from video_downloader.models.conversion import ConversionMode, ConversionRequest, MediaKind
from video_downloader.services.conversion_service import ConversionService


def make_request(tmp_path: Path, kind: MediaKind = MediaKind.VIDEO) -> ConversionRequest:
    src = tmp_path / "in.mp4"
    src.write_bytes(b"x")
    return ConversionRequest(
        source=src, target_format="mkv", kind=kind, mode=ConversionMode.REMUX
    )


def wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_video_conversion_success(tmp_path: Path):
    ffmpeg = mock.Mock()
    out = tmp_path / "in.mkv"

    def fake_convert(src, target, mode, on_progress, cancel_event):
        on_progress(0.5)
        on_progress(1.0)
        return out

    ffmpeg.convert_video.side_effect = fake_convert
    bus = EventBus()
    service = ConversionService(ffmpeg, bus)
    job = service.enqueue(make_request(tmp_path))

    assert wait_for(lambda: job.done)
    assert job.output_path == out
    assert job.error is None
    kinds = [type(e).__name__ for e in bus._pending]
    assert "ConversionProgress" in kinds
    finished = [e for e in bus._pending if isinstance(e, ConversionFinished)]
    assert finished and finished[0].output_path == out


def test_audio_conversion_routes_to_convert_audio(tmp_path: Path):
    ffmpeg = mock.Mock()
    ffmpeg.convert_audio.return_value = tmp_path / "in.mp3"
    service = ConversionService(ffmpeg, EventBus())
    request = make_request(tmp_path, kind=MediaKind.AUDIO)
    job = service.enqueue(request)
    assert wait_for(lambda: job.done)
    ffmpeg.convert_audio.assert_called_once()
    ffmpeg.convert_video.assert_not_called()


def test_conversion_failure_sets_error_key(tmp_path: Path):
    ffmpeg = mock.Mock()
    ffmpeg.convert_video.side_effect = ConversionError("boom")
    service = ConversionService(ffmpeg, EventBus())
    job = service.enqueue(make_request(tmp_path))
    assert wait_for(lambda: job.done)
    assert job.error == "error_conversion"


def test_delete_original_when_not_keeping(tmp_path: Path):
    ffmpeg = mock.Mock()
    ffmpeg.convert_video.return_value = tmp_path / "in.mkv"
    service = ConversionService(ffmpeg, EventBus())
    request = make_request(tmp_path)
    request.keep_original = False
    job = service.enqueue(request)
    assert wait_for(lambda: job.done)
    assert not request.source.exists()


def test_cancelled_before_start(tmp_path: Path):
    ffmpeg = mock.Mock()
    slow_started = threading.Event()

    def slow_convert(src, target, mode, on_progress, cancel_event):
        slow_started.set()
        time.sleep(0.3)
        return tmp_path / "a.mkv"

    ffmpeg.convert_video.side_effect = slow_convert
    service = ConversionService(ffmpeg, EventBus())
    first = service.enqueue(make_request(tmp_path))
    second = service.enqueue(make_request(tmp_path))
    slow_started.wait(timeout=5)
    service.cancel(second.id)
    assert wait_for(lambda: first.done and second.done)
    assert second.output_path is None
