"""Logging setup: console plus rotating file in the user log directory."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

import platformdirs

from video_downloader.config.constants import APP_AUTHOR, APP_NAME

_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def log_dir() -> Path:
    path = Path(platformdirs.user_log_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def setup_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if root.handlers:  # already configured (e.g. flet hot reload)
        return
    root.setLevel(level)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(console)

    file_handler = logging.handlers.RotatingFileHandler(
        log_dir() / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(file_handler)

    # yt-dlp is chatty at DEBUG through its own logger adapter
    logging.getLogger("ytdlp").setLevel(logging.INFO)
