"""Post-download conversion models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class ConversionMode(StrEnum):
    REMUX = "remux"  # container change only, lossless (-c copy)
    REENCODE = "reencode"  # full re-encode


class MediaKind(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"


@dataclass(slots=True)
class ConversionRequest:
    source: Path
    target_format: str  # container (video) or codec/format (audio)
    kind: MediaKind
    mode: ConversionMode
    audio_bitrate_kbps: int | None = None
    keep_original: bool = True
