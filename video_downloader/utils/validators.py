"""URL validation/classification and filename sanitizing."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)

# Characters not welcome in filenames on any platform
_FILENAME_BAD = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def is_valid_url(text: str) -> bool:
    text = text.strip()
    if not _URL_RE.match(text):
        return False
    parsed = urlparse(text)
    return bool(parsed.netloc)


def looks_like_playlist(url: str) -> bool:
    """Fast heuristic used only for UI hints; yt-dlp has the final word."""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if "youtube" in host or "youtu.be" in host:
        query = parse_qs(parsed.query)
        if "list" in query:
            return True
        if parsed.path.startswith(("/playlist", "/channel/", "/c/", "/user/")):
            return True
        if parsed.path.startswith("/@") and "/watch" not in parsed.path:
            return True
    return False


def sanitize_filename(name: str, max_length: int = 180) -> str:
    cleaned = _FILENAME_BAD.sub("_", name).strip().strip(".")
    return cleaned[:max_length] or "archivo"
