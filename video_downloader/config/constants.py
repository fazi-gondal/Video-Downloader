"""Application-wide constants and preset tables."""

from __future__ import annotations

APP_NAME = "VideoDownloader"
APP_AUTHOR = "Fazi Gondal"
APP_TITLE = "Video Downloader"
# Keep in sync with [project] version in pyproject.toml on every release
APP_VERSION = "1.0.0"

# Developer / project links shown in the About screen
DEVELOPER_NAME = "Faizan Gondal"
DEVELOPER_GITHUB_URL = "https://github.com/fazi-gondal"
DEVELOPER_LINKEDIN_URL = "https://www.linkedin.com/in/wachu985/"
DEVELOPER_WEBSITE_URL = "https://wachu985.hopto.net/"
REPO_URL = "https://github.com/fazi-gondal/Video-Downloader"
REPO_ISSUES_URL = f"{REPO_URL}/issues"

# Installation guide (INSTALL.md) with per-dependency anchors; the status
# cards in Settings deep-link here when a dependency is missing/partial.
INSTALL_GUIDE_URL = f"{REPO_URL}/blob/main/INSTALL.md"
INSTALL_FFMPEG_URL = f"{INSTALL_GUIDE_URL}#ffmpeg"
INSTALL_DENO_URL = f"{INSTALL_GUIDE_URL}#deno"

# Open-source license (shown/linked in the About screen)
APP_LICENSE = "MIT"
LICENSE_URL = f"{REPO_URL}/blob/main/LICENSE"

# Resolution presets: label -> max height (None = any/best)
RESOLUTION_PRESETS: dict[str, int | None] = {
    "Best available": None,
    "2160p (4K)": 2160,
    "1440p (2K)": 1440,
    "1080p": 1080,
    "720p": 720,
    "480p": 480,
    "360p": 360,
    "240p": 240,
    "144p": 144,
}

# FPS presets: label -> max fps (None = any)
FPS_PRESETS: dict[str, int | None] = {
    "Any": None,
    "60 fps": 60,
    "30 fps": 30,
}

# Video containers offered for download/merge
VIDEO_CONTAINERS: list[str] = ["mp4", "mkv", "webm"]

# Video containers offered for post-download conversion
CONVERSION_VIDEO_CONTAINERS: list[str] = ["mp4", "mkv", "webm", "avi"]

# Audio formats offered for extraction (must be valid FFmpegExtractAudio codecs)
AUDIO_FORMATS: list[str] = ["mp3", "m4a", "aac", "flac", "opus", "wav"]

# Audio quality presets: label -> kbps (None = best / keep source)
AUDIO_QUALITY_PRESETS: dict[str, int | None] = {
    "Best available": None,
    "320 kbps": 320,
    "256 kbps": 256,
    "192 kbps": 192,
    "128 kbps": 128,
}

# Lossless audio codecs where a bitrate makes no sense
LOSSLESS_AUDIO_FORMATS: frozenset[str] = frozenset({"flac", "wav"})

# Browsers supported by yt-dlp's cookiesfrombrowser
COOKIE_BROWSERS: list[str] = [
    "",  # disabled
    "chrome",
    "firefox",
    "safari",
    "edge",
    "brave",
    "opera",
    "vivaldi",
]

DEFAULT_MAX_CONCURRENT = 2
MAX_CONCURRENT_LIMIT = 8

# Hard UI cap for interactive URL analysis: even if yt-dlp hangs beyond its
# own (fail-fast) retries, the spinner never runs forever.
ANALYSIS_TIMEOUT_SECONDS = 75

# Output filename template for yt-dlp
OUTPUT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
PLAYLIST_OUTPUT_TEMPLATE = "%(playlist_title)s/%(playlist_index)03d - %(title)s [%(id)s].%(ext)s"

# Progress events forwarded to the UI at most this often per task (seconds)
PROGRESS_THROTTLE_SECONDS = 0.2
