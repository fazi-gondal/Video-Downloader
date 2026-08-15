"""Humanized formatting helpers; every input may be None."""

from __future__ import annotations

UNKNOWN = "desconocido"


def human_bytes(size: int | float | None, *, approx: bool = False) -> str:
    if size is None:
        return UNKNOWN
    prefix = "~" if approx else ""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            if unit == "B":
                return f"{prefix}{int(value)} {unit}"
            return f"{prefix}{value:.1f} {unit}"
        value /= 1024
    return UNKNOWN


def human_speed(bps: float | None) -> str:
    if bps is None:
        return "—"
    return f"{human_bytes(bps)}/s"


def human_eta(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def human_duration(seconds: float | None) -> str:
    if seconds is None:
        return UNKNOWN
    return human_eta(seconds)


def human_bitrate(kbps: float | None) -> str:
    if kbps is None:
        return "—"
    return f"{kbps:.0f} kbps"


def human_fps(fps: float | None) -> str:
    if fps is None:
        return "—"
    return f"{fps:.0f}"
