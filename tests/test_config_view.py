"""Tests for download configuration helpers."""

from pathlib import Path

from video_downloader.models.media import FormatInfo, StreamType
from video_downloader.ui.views.config_view import ConfigView, _playlist_download_dir


def make_format(
    format_id: str,
    ext: str,
    stream_type: StreamType,
    filesize: int,
    *,
    height: int | None = None,
    fps: float | None = None,
    vcodec: str | None = None,
    acodec: str | None = None,
    abr: float | None = None,
) -> FormatInfo:
    return FormatInfo(
        format_id=format_id,
        ext=ext,
        resolution=f"{height}p" if height else None,
        height=height,
        fps=fps,
        vcodec=vcodec,
        acodec=acodec,
        tbr=None,
        abr=abr,
        filesize=filesize,
        filesize_is_approx=False,
        stream_type=stream_type,
    )


def test_video_size_estimate_prefers_vp9_stream_when_enabled():
    mp4 = make_format(
        "137",
        "mp4",
        StreamType.VIDEO_ONLY,
        12_000,
        height=1080,
        fps=30,
        vcodec="avc1.640028",
    )
    webm = make_format(
        "248",
        "webm",
        StreamType.VIDEO_ONLY,
        10_000,
        height=1080,
        fps=30,
        vcodec="vp09.00.51.08",
    )

    selected = ConfigView._find_best_video_format(
        [mp4, webm], max_h=1080, max_fps=30, container="mp4", prefer_vp9=True
    )

    assert selected is webm


def test_video_size_estimate_uses_container_stream_without_vp9_preference():
    mp4 = make_format(
        "137",
        "mp4",
        StreamType.VIDEO_ONLY,
        12_000,
        height=1080,
        fps=30,
        vcodec="avc1.640028",
    )
    webm = make_format(
        "248",
        "webm",
        StreamType.VIDEO_ONLY,
        10_000,
        height=1080,
        fps=30,
        vcodec="vp09.00.51.08",
    )

    selected = ConfigView._find_best_video_format(
        [mp4, webm], max_h=1080, max_fps=30, container="mp4", prefer_vp9=False
    )

    assert selected is mp4


def test_audio_size_estimate_prefers_opus_when_vp9_downloads_are_preferred():
    m4a = make_format(
        "140",
        "m4a",
        StreamType.AUDIO_ONLY,
        4_000,
        acodec="mp4a.40.2",
        abr=128,
    )
    webm = make_format(
        "251",
        "webm",
        StreamType.AUDIO_ONLY,
        3_000,
        acodec="opus",
        abr=128,
    )

    selected = ConfigView._find_best_audio_format(
        [m4a, webm], container="mp4", prefer_opus=True
    )

    assert selected is webm


def test_playlist_download_dir_uses_sanitized_playlist_title():
    path = _playlist_download_dir(Path("downloads"), "My Playlist: 2026/Best")
    assert path == Path("downloads") / "My Playlist_ 2026_Best"
