"""Application error taxonomy and mapping from yt-dlp exceptions."""

from __future__ import annotations


class AppError(Exception):
    """Base class for errors surfaced to the user.

    ``user_message_key`` indexes into ``ui/texts.py`` so the UI always shows
    a Spanish message while logs keep the raw English detail.
    """

    user_message_key: str = "error_generic"

    def __init__(self, message: str = "", *, detail: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        self.detail = detail


class AnalysisError(AppError):
    user_message_key = "error_analysis"


class UnsupportedUrlError(AnalysisError):
    user_message_key = "error_unsupported_url"


class NetworkError(AppError):
    user_message_key = "error_network"


class AuthRequiredError(AnalysisError):
    user_message_key = "error_auth_required"


class GeoBlockedError(AnalysisError):
    user_message_key = "error_geo_blocked"


class LiveContentError(AnalysisError):
    user_message_key = "error_live_content"


class DownloadFailedError(AppError):
    user_message_key = "error_download_failed"


class FormatUnavailableError(AppError):
    user_message_key = "error_format_unavailable"


class PostProcessingError(AppError):
    user_message_key = "error_postprocessing"


class FFmpegNotFoundError(AppError):
    user_message_key = "error_ffmpeg_missing"


class ConversionError(AppError):
    user_message_key = "error_conversion"


class DownloadCancelled(Exception):  # noqa: N818 - control flow, not an error
    """Raised inside progress hooks to abort an in-flight download."""


_AUTH_MARKERS = (
    "sign in to confirm",
    "login required",
    "private video",
    "members-only",
    "age-restricted",
    "confirm your age",
    "cookies",
)
_NETWORK_MARKERS = (
    "unable to download",
    "connection",
    "timed out",
    "timeout",
    "temporary failure in name resolution",
    "getaddrinfo failed",
    "network",
    "http error 5",
    "proxy",
)
_LIVE_MARKERS = ("this live event", "live stream", "premieres in")


def map_ytdlp_error(exc: Exception) -> AppError:
    """Translate a yt-dlp exception into the application error taxonomy."""
    import yt_dlp.utils as ytu

    message = str(exc)
    lowered = message.lower()

    if isinstance(exc, ytu.GeoRestrictedError):
        return GeoBlockedError(message, detail=message)
    if isinstance(exc, ytu.UnsupportedError):
        return UnsupportedUrlError(message, detail=message)

    if "requested format is not available" in lowered or "only images are available" in lowered:
        return FormatUnavailableError(message, detail=message)
    if any(marker in lowered for marker in _AUTH_MARKERS):
        return AuthRequiredError(message, detail=message)
    if any(marker in lowered for marker in _LIVE_MARKERS):
        return LiveContentError(message, detail=message)
    if "is not a valid url" in lowered or "unsupported url" in lowered:
        return UnsupportedUrlError(message, detail=message)
    if any(marker in lowered for marker in _NETWORK_MARKERS):
        return NetworkError(message, detail=message)

    if isinstance(exc, ytu.ExtractorError):
        return AnalysisError(message, detail=message)
    if isinstance(exc, ytu.PostProcessingError):
        return PostProcessingError(message, detail=message)
    if isinstance(exc, ytu.DownloadError):
        return DownloadFailedError(message, detail=message)

    return AppError(message, detail=message)
