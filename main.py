"""Entry point for the Video Downloader desktop app."""

from __future__ import annotations

import logging
import sys
import traceback

import flet as ft

from video_downloader.config.constants import APP_TITLE
from video_downloader.core.logging_config import log_dir, setup_logging
from video_downloader.ui.app import main
from video_downloader.utils.env import ensure_common_paths

logger = logging.getLogger(__name__)


def _show_startup_error(exc: BaseException) -> None:
    """Surface fatal boot errors when launched from a desktop shortcut."""
    try:
        log_path = log_dir() / "app.log"
    except Exception:
        log_path = None

    details = "".join(traceback.format_exception_only(type(exc), exc)).strip()
    message = f"{APP_TITLE} could not start.\n\n{details}"
    if log_path is not None:
        message += f"\n\nLog file:\n{log_path}"

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, APP_TITLE, 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


if __name__ == "__main__":
    try:
        ensure_common_paths()
        setup_logging()
        ft.run(main, assets_dir="assets")
    except Exception as exc:
        logger.exception("Fatal startup error")
        _show_startup_error(exc)
        raise
