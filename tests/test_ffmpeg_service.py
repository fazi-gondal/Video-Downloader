"""FFmpeg toolchain resolution and remux-decision tests (no real ffmpeg runs)."""

from pathlib import Path
from unittest import mock

from video_downloader.models.conversion import ConversionMode
from video_downloader.services.ffmpeg_service import FFmpegService

_NO_STATIC = mock.patch(
    "video_downloader.services.ffmpeg_service._static_ffmpeg_paths", return_value=None
)


def test_resolves_system_ffmpeg():
    service = FFmpegService()
    with mock.patch("shutil.which", side_effect=lambda name: f"/usr/local/bin/{name}"):
        location = service.resolve()
    assert location.source == "path"
    assert location.ffmpeg_path == Path("/usr/local/bin/ffmpeg")
    assert location.ffprobe_path == Path("/usr/local/bin/ffprobe")
    assert service.is_available
    # both binaries in the same dir -> pass the directory to yt-dlp
    assert service.ytdlp_location_arg() == str(Path("/usr/local/bin"))


def test_static_toolchain_preferred_over_imageio():
    service = FFmpegService()
    static = (Path("/static/bin/ffmpeg"), Path("/static/bin/ffprobe"))
    with mock.patch("shutil.which", return_value=None), mock.patch(
        "video_downloader.services.ffmpeg_service._static_ffmpeg_paths",
        return_value=static,
    ):
        location = service.resolve()
    assert location.source == "bundled_full"
    assert service.has_ffprobe
    assert service.ytdlp_location_arg() == str(Path("/static/bin"))


def test_falls_back_to_imageio_bundled():
    service = FFmpegService()
    with mock.patch("shutil.which", return_value=None), _NO_STATIC, mock.patch(
        "imageio_ffmpeg.get_ffmpeg_exe", return_value="/bundle/ffmpeg"
    ):
        location = service.resolve()
    assert location.source == "bundled"
    assert location.ffmpeg_path == Path("/bundle/ffmpeg")
    assert location.ffprobe_path is None
    assert not service.has_ffprobe
    # no ffprobe alongside -> pass the ffmpeg binary itself
    assert service.ytdlp_location_arg() == str(Path("/bundle/ffmpeg"))


def test_missing_everywhere():
    service = FFmpegService()
    with mock.patch("shutil.which", return_value=None), _NO_STATIC, mock.patch(
        "imageio_ffmpeg.get_ffmpeg_exe", side_effect=RuntimeError("no binary")
    ):
        location = service.resolve()
    assert location.source == "missing"
    assert not service.is_available
    assert service.ytdlp_location_arg() is None


def test_resolution_is_cached_and_invalidate_resets():
    service = FFmpegService()
    with mock.patch("shutil.which", side_effect=lambda name: f"/usr/bin/{name}") as which:
        service.resolve()
        service.resolve()
        assert which.call_count == 2  # ffmpeg + ffprobe, only on first resolve
        service.invalidate()
        service.resolve()
        assert which.call_count == 4


def test_can_remux_with_ffprobe_data():
    service = FFmpegService()
    probe = {
        "streams": [
            {"codec_type": "video", "codec_name": "h264"},
            {"codec_type": "audio", "codec_name": "aac"},
        ]
    }
    with mock.patch.object(service, "probe", return_value=probe):
        assert service.can_remux(Path("v.mkv"), "mp4")
        assert not service.can_remux(Path("v.mkv"), "webm")  # h264 no cabe en webm


def test_can_remux_heuristic_without_ffprobe():
    service = FFmpegService()
    with mock.patch.object(service, "probe", return_value=None):
        assert service.can_remux(Path("v.mp4"), "mkv")
        assert service.can_remux(Path("v.mp4"), "mp4")
        assert not service.can_remux(Path("v.mp4"), "avi")


def test_conversion_mode_enum():
    assert ConversionMode.REMUX.value == "remux"
    assert ConversionMode.REENCODE.value == "reencode"
