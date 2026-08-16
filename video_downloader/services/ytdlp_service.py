"""yt-dlp integration: analysis, format listing and blocking downloads.

Everything here is blocking and must run on a worker thread (or via
``asyncio.to_thread`` for the short-lived analysis calls). No Flet objects:
progress is reported through callbacks/events only.
"""

from __future__ import annotations

import logging
import tempfile
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
from video_downloader.models.download import (
    DownloadMode,
    DownloadState,
    DownloadTask,
    ProgressInfo,
)
from video_downloader.models.media import FormatInfo, MediaInfo, PlaylistInfo
from video_downloader.services import format_builder
from video_downloader.services.ffmpeg_service import FFmpegService
from video_downloader.services.format_builder import (
    _LANG_CODE_RE,
    _audio_selector,
    _get_js_runtimes,
)
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
        # Multi-audio custom selection: each track downloaded separately then merged,
        # because yt-dlp's audio_multistreams deduplicates same-itag streams even
        # when they carry different language labels.
        req = task.request
        if (
            req.mode is DownloadMode.VIDEO_AUDIO
            and len(req.selected_audio_track_ids) > 1
        ):
            return self._download_multi_audio(task, bus)
        return self._download_single(task, bus)

    def _download_single(self, task: DownloadTask, bus: EventBus) -> Path:
        """Standard single yt-dlp call for non-multi-audio downloads."""
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

    def _download_multi_audio(self, task: DownloadTask, bus: EventBus) -> Path:
        """Download video + multiple audio tracks separately, then merge with FFmpeg.

        yt-dlp's ``audio_multistreams`` flag cannot download two opus-251 streams
        (one per language) in a single call — it deduplicates them.  The only
        working approach is:

        1. Download video + first selected audio: ``bv*+ba[language=XX]`` → main.mkv
        2. For each remaining language:  ``ba[language=YY]``          → audioN.webm
        3. FFmpeg copy-mux everything into the final output MKV.
        """
        import yt_dlp

        req = task.request
        settings = self._settings_provider()
        track_ids = list(req.selected_audio_track_ids)  # e.g. ["en", "de", "ja"]

        def _make_base_opts(outtmpl: str) -> dict[str, Any]:
            """Base yt-dlp opts shared by all passes (no postprocessors)."""
            o: dict[str, Any] = {
                "noplaylist": True,
                "continuedl": True,
                "retries": 5,
                "fragment_retries": 5,
                "socket_timeout": 30,
                "extractor_retries": 3,
                "quiet": True,
                "noprogress": True,
                "no_color": True,
                "windowsfilenames": False,
                "restrictfilenames": False,
                "remote_components": ["ejs:github"],
                "js_runtimes": _get_js_runtimes(),
                "extractor_args": {"youtube": {"player_client": ["all"]}},
                "outtmpl": outtmpl,
                "logger": ytdlp_logger,
            }
            if ffmpeg_loc := self._ffmpeg.ytdlp_location_arg():
                o["ffmpeg_location"] = ffmpeg_loc
            if settings.proxy:
                o["proxy"] = settings.proxy
            if settings.cookies_browser:
                o["cookiesfrombrowser"] = (settings.cookies_browser,)
            return o

        def _make_progress_hook(pass_index: int) -> Callable[[dict[str, Any]], None]:
            """Return a progress hook that weights this pass proportionally."""
            nonlocal last_emit
            def hook(d: dict[str, Any]) -> None:
                nonlocal last_emit
                if task.cancel_event.is_set():
                    raise DownloadCancelled()
                status = d.get("status")
                now = time.monotonic()
                if status == "downloading":
                    if task.state is not DownloadState.DOWNLOADING:
                        task.state = DownloadState.DOWNLOADING
                        bus.publish(
                            TaskStateChanged(
                                task_id=task.id, state=DownloadState.DOWNLOADING
                            )
                        )
                    if now - last_emit < PROGRESS_THROTTLE_SECONDS:
                        return
                    last_emit = now
                    total = d.get("total_bytes") or d.get("total_bytes_estimate")
                    downloaded = d.get("downloaded_bytes")
                    progress = ProgressInfo(
                        downloaded_bytes=downloaded,
                        total_bytes=total,
                        total_is_estimate=d.get("total_bytes") is None,
                        speed_bps=d.get("speed"),
                        eta_seconds=d.get("eta"),
                    )
                    task.progress = progress
                    bus.publish(TaskProgress(task_id=task.id, progress=progress))
                elif status == "finished":
                    task.state = DownloadState.PROCESSING
                    bus.publish(TaskStateChanged(task_id=task.id, state=DownloadState.PROCESSING))
            return hook

        last_emit = 0.0

        with tempfile.TemporaryDirectory(prefix="vd_multiaudio_") as tmpdir:
            tmp = Path(tmpdir)

            # ── Pass 0: video + first audio track ──────────────────────────
            first_selector = _audio_selector(track_ids[0])
            filters = ""
            if req.max_height:
                filters += f"[height<=?{req.max_height}]"
            if req.max_fps:
                filters += f"[fps<=?{req.max_fps}]"
            video_part = req.video_format_id or (f"bv*{filters}" if filters else "bv*")
            main_fmt = f"{video_part}+{first_selector}/{video_part}+ba/b"

            outtmpl_pattern = format_builder.build_output_template(req)
            main_opts = _make_base_opts(str(tmp / outtmpl_pattern))
            main_opts["format"] = main_fmt
            main_opts["merge_output_format"] = "mkv"
            main_opts["audio_multistreams"] = False
            if req.prefer_vp9_video and not req.video_format_id:
                main_opts["format_sort"] = list(format_builder.VP9_FORMAT_SORT)
            main_opts["progress_hooks"] = [_make_progress_hook(0)]
            main_opts["postprocessors"] = format_builder.build_postprocessors(
                req, have_ffprobe=self._ffmpeg.has_ffprobe
            )
            if req.write_subtitles:
                main_opts["writesubtitles"] = True
                main_opts["writeautomaticsub"] = True
                if not req.subtitle_langs or "all" in req.subtitle_langs:
                    main_opts["subtitleslangs"] = ["all"]
                else:
                    main_opts["subtitleslangs"] = list(req.subtitle_langs)
            if req.embed_thumbnail:
                main_opts["writethumbnail"] = True

            main_info: dict[str, Any] | None = None
            try:
                with yt_dlp.YoutubeDL(main_opts) as ydl:
                    main_info = ydl.extract_info(req.url, download=True)
            except DownloadCancelled:
                raise
            except Exception as exc:
                if task.cancel_event.is_set():
                    raise DownloadCancelled() from exc
                raise map_ytdlp_error(exc) from exc

            # Locate the downloaded main file
            main_file: Path | None = None
            if main_info:
                rq = main_info.get("requested_downloads") or []
                if rq and rq[0].get("filepath"):
                    main_file = Path(rq[0]["filepath"])
                elif main_info.get("filepath"):
                    main_file = Path(main_info["filepath"])
            if main_file is None:
                candidates = [
                    p for p in tmp.iterdir()
                    if not p.name.startswith("audio") and p.is_file()
                ]
                if candidates:
                    main_file = max(candidates, key=lambda p: p.stat().st_size)
            if main_file is None or not main_file.exists():
                raise AppError("Multi-audio pass 0: output file not found")

            # ── Passes 1…N: one audio-only download per additional track ───
            extra_audio: list[tuple[Path, str]] = []
            for i, track_key in enumerate(track_ids[1:], start=1):
                if task.cancel_event.is_set():
                    raise DownloadCancelled()

                audio_fmt = f"{_audio_selector(track_key)}/ba"
                audio_opts = _make_base_opts(str(tmp / f"audio{i}.%(ext)s"))
                audio_opts["format"] = audio_fmt
                audio_opts["progress_hooks"] = [_make_progress_hook(i)]

                audio_info: dict[str, Any] | None = None
                try:
                    with yt_dlp.YoutubeDL(audio_opts) as ydl:
                        audio_info = ydl.extract_info(req.url, download=True)
                except DownloadCancelled:
                    raise
                except Exception as exc:
                    if task.cancel_event.is_set():
                        raise DownloadCancelled() from exc
                    logger.warning(
                        "Multi-audio pass %d failed (%s), skipping track %s",
                        i,
                        exc,
                        track_key,
                    )
                    continue

                audio_file: Path | None = None
                if audio_info:
                    rq = audio_info.get("requested_downloads") or []
                    if rq and rq[0].get("filepath"):
                        audio_file = Path(rq[0]["filepath"])
                    elif audio_info.get("filepath"):
                        audio_file = Path(audio_info["filepath"])
                if audio_file is None:
                    candidates = list(tmp.glob(f"audio{i}.*"))
                    if candidates:
                        audio_file = max(candidates, key=lambda p: p.stat().st_size)
                if audio_file and audio_file.exists():
                    # Language tag for metadata: use raw track_key if it's a lang code
                    lang_tag = track_key if _LANG_CODE_RE.match(track_key) else ""
                    extra_audio.append((audio_file, lang_tag))
                else:
                    logger.warning("Multi-audio pass %d: output not found, skipping", i)

            # ── Final merge ─────────────────────────────────────────────────
            task.state = DownloadState.PROCESSING
            bus.publish(TaskStateChanged(task_id=task.id, state=DownloadState.PROCESSING))

            output_dir = Path(req.output_dir).expanduser()
            output_dir.mkdir(parents=True, exist_ok=True)
            # Derive output filename from main file stem (e.g. "Video Title [id].mkv")
            output_path = output_dir / (main_file.stem + ".mkv")

            if not extra_audio:
                # No extra tracks were downloaded successfully — just move the main file
                import shutil
                shutil.move(str(main_file), str(output_path))
                return output_path

            first_lang_tag = track_ids[0] if _LANG_CODE_RE.match(track_ids[0]) else ""
            self._ffmpeg.merge_audio_tracks(
                base_file=main_file,
                extra_audio=extra_audio,
                output=output_path,
                first_lang=first_lang_tag,
                cancel_event=task.cancel_event,
            )
            return output_path

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
