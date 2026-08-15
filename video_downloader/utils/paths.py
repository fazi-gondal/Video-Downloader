"""Filesystem path helpers."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def default_download_dir() -> Path:
    downloads = Path.home() / "Downloads"
    if downloads.is_dir():
        return downloads / "VideoDownloader"
    return Path.home() / "VideoDownloader"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def open_in_file_manager(path: Path) -> None:
    """Reveal *path* in the OS file manager (best effort)."""
    target = path if path.is_dir() else path.parent
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(target)], check=False)
        elif sys.platform.startswith("win"):
            subprocess.run(["explorer", str(target)], check=False)
        else:
            subprocess.run(["xdg-open", str(target)], check=False)
    except OSError as exc:
        logger.warning("Could not open file manager for %s: %s", target, exc)


def unique_path(path: Path) -> Path:
    """Return *path*, or a ``name (n).ext`` variant that does not exist yet."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for n in range(1, 1000):
        candidate = path.with_name(f"{stem} ({n}){suffix}")
        if not candidate.exists():
            return candidate
    raise FileExistsError(f"Could not find a unique name for {path}")
