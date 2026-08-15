"""yt-dlp integration: analysis, format listing and blocking downloads.

Everything here is blocking and must run on a worker thread (or via
``asyncio.to_thread`` for the short-lived analysis calls). No Flet objects:
progress is reported through callbacks/events only.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from video_downloader.config.constants import PROGRESS_THROTTLE_SECONDS
from video_downloader.config.settings import AppSettings
from video_downloader.core.errors import (
    AppError,
    DownloadCancelled,
    UnsupportedUrlError,
    map_ytdlp_error,
)
from video_downloader.core.event_bus import EventBus
from video_downloader.core.events import TaskPostProcessing, TaskProgress, TaskStateChanged
from video_downloader.models.download import DownloadState, DownloadTask, ProgressInfo
from video_downloader.models.media import FormatInfo, MediaInfo, PlaylistInfo
from video_downloader.services import format_builder
from video_downloader.services.ffmpeg_service import FFmpegService
from video_downloader.utils.validators import is_valid_url

logger = logging.getLogger(__name__)
ytdlp_logger = logging.getLogger("ytdlp")


class YtdlpService:
    def __init__(
        self,
        ffmpeg: FFmpegService,
        settings_provider: Callable[[], AppSettings],
    ) -> None:
        self._ffmpeg = ffmpeg
        self._settings_provider = settings_provider

    # ------------------------------------------------------------------
    # Analysis

    def analyze(self, url: str) -> MediaInfo | PlaylistInfo:
        """Fast analysis of *url*: playlist entries come from flat extraction."""
        url = url.strip()
        if not is_valid_url(url):
            raise UnsupportedUrlError(f"Not a valid URL: {url!r}")

        opts = format_builder.build_analysis_opts(self._settings_provider())
        opts["logger"] = ytdlp_logger
        info = self._extract(url, opts)

        if info.get("_type") == "playlist":
            return PlaylistInfo.from_ytdlp(info)
        return MediaInfo.from_ytdlp(info)

    def fetch_formats(self, url: str) -> MediaInfo:
        """Full (non-flat) extraction of a single video, including formats."""
        opts = format_builder.build_analysis_opts(self._settings_provider())
        opts.pop("extract_flat", None)
        opts["noplaylist"] = True
        opts["logger"] = ytdlp_logger
        info = self._extract(url, opts)
        if info.get("_type") == "playlist":
            entries = [e for e in info.get("entries") or [] if e]
            if not entries:
                raise UnsupportedUrlError("Playlist has no entries")
            info = entries[0]
        return MediaInfo.from_ytdlp(info)

    @staticmethod
    def _extract(url: str, opts: dict[str, Any]) -> dict[str, Any]:
        import yt_dlp

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Extraction failed for %s", url)
            raise map_ytdlp_error(exc) from exc
        if info is None:
            raise UnsupportedUrlError(f"No information extracted for {url!r}")
        return info

    # ------------------------------------------------------------------
    # Download (blocking; runs on a DownloadManager worker thread)

    def download(self, task: DownloadTask, bus: EventBus) -> Path:
        """Download *task* publishing progress events; returns the final path."""
        import yt_dlp

        settings = self._settings_provider()
        opts = format_builder.build_ydl_opts(
            task.request,
            settings,
            self._ffmpeg.ytdlp_location_arg(),
            logger=ytdlp_logger,
            have_ffprobe=self._ffmpeg.has_ffprobe,
        )

        last_emit = 0.0
        final_path: dict[str, Path | None] = {"value": None}

        def progress_hook(d: dict[str, Any]) -> None:
            nonlocal last_emit
            if task.cancel_event.is_set():
                raise DownloadCancelled()

            status = d.get("status")
            now = time.monotonic()
            if status == "downloading":
                if task.state is not DownloadState.DOWNLOADING:
                    task.state = DownloadState.DOWNLOADING
                    bus.publish(
                        TaskStateChanged(task_id=task.id, state=DownloadState.DOWNLOADING)
                    )
                if now - last_emit < PROGRESS_THROTTLE_SECONDS:
                    return
                last_emit = now
                total = d.get("total_bytes")
                is_estimate = False
                if total is None:
                    total = d.get("total_bytes_estimate")
                    is_estimate = total is not None
                progress = ProgressInfo(
                    downloaded_bytes=d.get("downloaded_bytes"),
                    total_bytes=total,
                    total_is_estimate=is_estimate,
                    speed_bps=d.get("speed"),
                    eta_seconds=d.get("eta"),
                )
                task.progress = progress
                bus.publish(TaskProgress(task_id=task.id, progress=progress))
            elif status == "finished":
                filename = d.get("filename")
                if filename:
                    final_path["value"] = Path(filename)
                # Postprocessing (merge/convert) may follow; a further DASH
                # stream flips the state back to DOWNLOADING in this hook.
                task.state = DownloadState.PROCESSING
                bus.publish(
                    TaskStateChanged(task_id=task.id, state=DownloadState.PROCESSING)
                )

        def postprocessor_hook(d: dict[str, Any]) -> None:
            if task.cancel_event.is_set():
                raise DownloadCancelled()
            if d.get("status") == "started":
                bus.publish(
                    TaskPostProcessing(
                        task_id=task.id, processor=d.get("postprocessor") or ""
                    )
                )
            elif d.get("status") == "finished":
                info = d.get("info_dict") or {}
                filepath = info.get("filepath")
                if filepath:
                    final_path["value"] = Path(filepath)

        opts["progress_hooks"] = [progress_hook]
        opts["postprocessor_hooks"] = [postprocessor_hook]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(task.request.url, download=True)
        except DownloadCancelled:
            raise
        except Exception as exc:
            if task.cancel_event.is_set():
                # yt-dlp wraps hook exceptions in DownloadError; recover intent
                raise DownloadCancelled() from exc
            raise map_ytdlp_error(exc) from exc

        # Prefer paths reported by yt-dlp's own bookkeeping
        if info:
            requested = info.get("requested_downloads") or []
            if requested and requested[0].get("filepath"):
                return Path(requested[0]["filepath"])
            if info.get("filepath"):
                return Path(info["filepath"])
        if final_path["value"] is not None:
            return final_path["value"]
        raise AppError("Download finished but output path is unknown")

    # ------------------------------------------------------------------

    @staticmethod
    def cleanup_partials(output_dir: Path, media_id: str) -> None:
        """Remove ``.part``/``.ytdl`` leftovers for a cancelled download."""
        try:
            for pattern in (f"*{media_id}*.part", f"*{media_id}*.ytdl", f"*{media_id}*.part-Frag*"):
                for leftover in output_dir.glob(pattern):
                    leftover.unlink(missing_ok=True)
                    logger.info("Removed partial file %s", leftover)
        except OSError as exc:
            logger.warning("Could not clean partial files: %s", exc)


def formats_for_display(media: MediaInfo) -> list[FormatInfo]:
    """Formats sorted for the explorer table: muxed, video desc, audio desc."""
    def sort_key(f: FormatInfo) -> tuple[int, float, float]:
        type_order = {"muxed": 0, "video": 1, "audio": 2}[f.stream_type.value]
        return (type_order, -(f.height or 0), -(f.tbr or f.abr or 0))

    return sorted(media.formats, key=sort_key)
