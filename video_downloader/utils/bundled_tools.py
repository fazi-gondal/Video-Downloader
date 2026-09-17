"""Resolution helpers for binaries bundled with packaged app builds."""

from __future__ import annotations

import sys
from pathlib import Path

from video_downloader.config.constants import BUNDLED_TOOLS_DIR


def _tool_filename(name: str) -> str:
    if sys.platform.startswith("win") and not name.lower().endswith(".exe"):
        return f"{name}.exe"
    return name


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []
    executable_dir = Path(sys.executable).resolve().parent
    roots.append(executable_dir)
    roots.append(Path.cwd())

    # Source checkout root: video_downloader/utils/bundled_tools.py -> project root.
    roots.append(Path(__file__).resolve().parents[2])

    # Flet/PyInstaller-style launchers sometimes expose unpacked resources here.
    if frozen_root := getattr(sys, "_MEIPASS", None):
        roots.append(Path(frozen_root))

    unique: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        if resolved not in seen:
            unique.append(resolved)
            seen.add(resolved)
    return unique


def find_bundled_tool(name: str) -> Path | None:
    """Return a bundled executable path, or None when this build has no copy."""
    filename = _tool_filename(name)
    for root in _candidate_roots():
        candidate = root / BUNDLED_TOOLS_DIR / filename
        if candidate.is_file():
            return candidate
    return None
