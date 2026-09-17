"""Process environment helpers (PATH hardening, JS runtime detection)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from video_downloader.config.constants import BUNDLED_DENO_NAME
from video_downloader.utils.bundled_tools import find_bundled_tool

# Locations that GUI apps launched from Finder/Dock don't inherit
_EXTRA_PATHS_DARWIN = (
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "~/.deno/bin",
    "~/.bun/bin",
)

# Runtimes supported by yt-dlp's EJS challenge solver, in priority order
JS_RUNTIMES = ("deno", "node", "bun", "quickjs")


def find_executable(name: str) -> Path | None:
    """Return an app-bundled executable first, then a system PATH executable."""
    if name == BUNDLED_DENO_NAME and (bundled := find_bundled_tool(BUNDLED_DENO_NAME)):
        return bundled
    if located := shutil.which(name):
        return Path(located)
    return None


def ensure_common_paths() -> None:
    """Prepend well-known binary dirs to PATH when missing.

    A packaged .app inherits a minimal PATH from launchd, hiding Homebrew
    binaries such as ffmpeg and deno; terminal launches are unaffected.
    """
    if sys.platform != "darwin":
        return
    current = os.environ.get("PATH", "").split(os.pathsep)
    additions = [
        expanded
        for path in _EXTRA_PATHS_DARWIN
        if (expanded := str(Path(path).expanduser())) not in current
        and Path(expanded).is_dir()
    ]
    if additions:
        os.environ["PATH"] = os.pathsep.join([*current, *additions])


def find_js_runtime() -> tuple[str, Path] | None:
    """Return the first available (name, path) JS runtime, or None."""
    for name in JS_RUNTIMES:
        located = find_executable(name)
        if located:
            return name, located
    return None
