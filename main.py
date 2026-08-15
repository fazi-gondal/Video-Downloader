"""Entry point for the Video Downloader desktop app."""

import flet as ft

from video_downloader.core.logging_config import setup_logging
from video_downloader.ui.app import main
from video_downloader.utils.env import ensure_common_paths

if __name__ == "__main__":
    ensure_common_paths()
    setup_logging()
    ft.run(main, assets_dir="assets")
