"""Download request/task models and state machine."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path


class DownloadState(StrEnum):
    PENDING = "pending"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


TERMINAL_STATES: frozenset[DownloadState] = frozenset(
    {DownloadState.COMPLETED, DownloadState.ERROR, DownloadState.CANCELLED}
)


class DownloadMode(StrEnum):
    VIDEO_ONLY = "video"
    AUDIO_ONLY = "audio"
    VIDEO_AUDIO = "video_audio"


@dataclass(slots=True)
class DownloadRequest:
    """Everything needed to perform one download (one video)."""

    url: str
    title: str
    mode: DownloadMode
    output_dir: Path

    # Video options
    container: str = "mp4"  # target container for video / merge
    max_height: int | None = None  # resolution preset, None = best
    max_fps: int | None = None

    # Audio options
    audio_format: str = "mp3"
    audio_bitrate_kbps: int | None = None  # None = best

    # Explicit format selection (overrides presets when set)
    video_format_id: str | None = None
    audio_format_id: str | None = None

    # Extras
    write_subtitles: bool = False
    subtitle_langs: tuple[str, ...] = ("all",)
    multi_audio: bool = False
    selected_audio_track_ids: tuple[str, ...] = ()
    embed_thumbnail: bool = True
    embed_metadata: bool = False
    prefer_vp9_video: bool = False

    # Playlist context (affects output template)
    playlist_title: str | None = None
    playlist_index: int | None = None

    # UI-only: thumbnail shown in the downloads list (not sent to yt-dlp)
    thumbnail_url: str | None = None


@dataclass(slots=True)
class ProgressInfo:
    """Snapshot of download progress; every field may be unknown."""

    downloaded_bytes: int | None = None
    total_bytes: int | None = None
    total_is_estimate: bool = False
    speed_bps: float | None = None
    eta_seconds: float | None = None

    @property
    def percent(self) -> float | None:
        if self.downloaded_bytes is None or not self.total_bytes:
            return None
        return min(1.0, self.downloaded_bytes / self.total_bytes)


@dataclass
class DownloadTask:
    """A queued/running download with its live state."""

    request: DownloadRequest
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: DownloadState = DownloadState.PENDING
    progress: ProgressInfo = field(default_factory=ProgressInfo)
    error: str | None = None  # user_message_key of the mapped AppError
    error_detail: str | None = None
    output_path: Path | None = None
    cancel_event: threading.Event = field(default_factory=threading.Event)
    created_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def is_active(self) -> bool:
        return not self.is_terminal
