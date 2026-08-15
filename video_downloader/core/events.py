"""Typed application events flowing from services to the UI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from video_downloader.models.download import DownloadState, ProgressInfo


@dataclass(slots=True, frozen=True)
class AppEvent:
    """Base class for all events published on the EventBus."""


@dataclass(slots=True, frozen=True)
class TaskEvent(AppEvent):
    task_id: str


@dataclass(slots=True, frozen=True)
class TaskQueued(TaskEvent):
    pass


@dataclass(slots=True, frozen=True)
class TaskStateChanged(TaskEvent):
    state: DownloadState
    error_key: str | None = None
    output_path: Path | None = None


@dataclass(slots=True, frozen=True)
class TaskProgress(TaskEvent):
    progress: ProgressInfo


@dataclass(slots=True, frozen=True)
class TaskPostProcessing(TaskEvent):
    processor: str  # e.g. "ExtractAudio", "Merger"


@dataclass(slots=True, frozen=True)
class ConversionQueued(TaskEvent):
    pass


@dataclass(slots=True, frozen=True)
class ConversionProgress(TaskEvent):
    percent: float | None


@dataclass(slots=True, frozen=True)
class ConversionFinished(TaskEvent):
    output_path: Path | None
    error_key: str | None = None


@dataclass(slots=True, frozen=True)
class FFmpegToolchainReady(AppEvent):
    """The background download of the full ffmpeg+ffprobe toolchain finished."""
