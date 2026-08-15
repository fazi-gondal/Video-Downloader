"""yt-dlp exception -> app error taxonomy mapping tests."""

import yt_dlp.utils as ytu

from video_downloader.core.errors import (
    AuthRequiredError,
    DownloadFailedError,
    GeoBlockedError,
    NetworkError,
    UnsupportedUrlError,
    map_ytdlp_error,
)


def test_geo_restricted():
    exc = ytu.GeoRestrictedError("blocked in your country")
    assert isinstance(map_ytdlp_error(exc), GeoBlockedError)


def test_unsupported_url():
    exc = ytu.UnsupportedError("https://example.com/nope")
    assert isinstance(map_ytdlp_error(exc), UnsupportedUrlError)


def test_auth_required_from_message():
    exc = ytu.DownloadError("ERROR: Sign in to confirm your age")
    assert isinstance(map_ytdlp_error(exc), AuthRequiredError)


def test_private_video_maps_to_auth():
    exc = ytu.DownloadError("Private video. Sign in if you've been granted access")
    assert isinstance(map_ytdlp_error(exc), AuthRequiredError)


def test_network_error_from_message():
    exc = ytu.DownloadError("unable to download video data: <urlopen error timed out>")
    assert isinstance(map_ytdlp_error(exc), NetworkError)


def test_format_unavailable_maps_to_js_challenge_hint():
    from video_downloader.core.errors import FormatUnavailableError

    exc = ytu.DownloadError(
        "ERROR: [youtube] abc: Requested format is not available. "
        "Use --list-formats for a list of available formats"
    )
    assert isinstance(map_ytdlp_error(exc), FormatUnavailableError)


def test_generic_download_error():
    exc = ytu.DownloadError("something odd happened")
    assert isinstance(map_ytdlp_error(exc), DownloadFailedError)


def test_error_keys_exist_in_texts():
    from video_downloader.core import errors
    from video_downloader.ui.texts import TEXTS

    for name in dir(errors):
        obj = getattr(errors, name)
        if isinstance(obj, type) and issubclass(obj, errors.AppError):
            assert obj.user_message_key in TEXTS, f"{name} key missing in texts"
