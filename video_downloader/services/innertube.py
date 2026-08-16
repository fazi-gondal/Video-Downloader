"""Direct YouTube InnerTube API client for multi-audio-track discovery.

yt-dlp's default client extraction only shows the audio tracks served to the
current session — usually just the original language.  YouTube's own InnerTube
``/youtubei/v1/player`` endpoint returns the *full* ``adaptiveFormats`` list,
including every dubbed/alternate audio track, when called with the right
``clientName``.  This is exactly what NewPipeExtractor does.

This module hits that endpoint directly (no authentication required for public
videos), parses every ``audioTrack`` field, and returns a merged list of audio
track dicts compatible with ``MediaInfo.audio_tracks``.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# InnerTube clients – we try each in order until we get at least one dubbed
# audio track.  ANDROID_VR and WEB_EMBEDDED reliably expose all dub streams.
# ──────────────────────────────────────────────────────────────────────────────
_INNERTUBE_CLIENTS: list[dict[str, Any]] = [
    {
        "clientName": "ANDROID_VR",
        "clientVersion": "1.60.19",
        "userAgent": (
            "com.google.android.apps.youtube.vr.oculus/1.60.19"
            " (Linux; U; Android 12L; eureka-user Build/SQ3A.220605.009.A1) gzip"
        ),
        "androidSdkVersion": 32,
        "osName": "Android",
        "osVersion": "12",
    },
    {
        "clientName": "WEB_EMBEDDED_PLAYER",
        "clientVersion": "2.20231206.00.00",
        "userAgent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/120.0.0.0 Safari/537.36"
        ),
    },
    {
        "clientName": "IOS",
        "clientVersion": "19.09.3",
        "userAgent": (
            "com.google.ios.youtube/19.09.3"
            " (iPhone16,2; U; CPU iPhone OS 17_3_1 like Mac OS X;)"
        ),
        "deviceModel": "iPhone16,2",
        "osName": "iPhone",
        "osVersion": "17.3.1.21E236",
    },
    {
        "clientName": "WEB",
        "clientVersion": "2.20231206.04.00",
        "userAgent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            " AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/120.0.0.0 Safari/537.36"
        ),
    },
]

_INNERTUBE_URL = "https://www.youtube.com/youtubei/v1/player?prettyPrint=false"
_VIDEO_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:watch\?.*?v=|embed/|v/|shorts/))([A-Za-z0-9_-]{11})"
)

_LANGUAGE_NAMES: dict[str, str] = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ja": "Japanese", "ko": "Korean",
    "zh": "Chinese", "ar": "Arabic", "ru": "Russian", "hi": "Hindi",
    "tr": "Turkish", "nl": "Dutch", "pl": "Polish", "sv": "Swedish",
    "da": "Danish", "fi": "Finnish", "nb": "Norwegian", "cs": "Czech",
    "sk": "Slovak", "hu": "Hungarian", "ro": "Romanian", "el": "Greek",
    "uk": "Ukrainian", "id": "Indonesian", "ms": "Malay", "th": "Thai",
    "vi": "Vietnamese", "fa": "Persian", "ur": "Urdu", "bn": "Bengali",
    "ta": "Tamil", "te": "Telugu", "ml": "Malayalam", "mr": "Marathi",
    "kn": "Kannada", "gu": "Gujarati", "pa": "Punjabi",
}


def _video_id(url: str) -> str | None:
    m = _VIDEO_ID_RE.search(url)
    return m.group(1) if m else None


def _innertube_request(video_id: str, client_ctx: dict[str, Any]) -> dict[str, Any]:
    """POST to InnerTube /player and return the parsed JSON."""
    body = json.dumps({
        "videoId": video_id,
        "context": {
            "client": {
                **client_ctx,
                "hl": "en",
                "gl": "US",
                "utcOffsetMinutes": 0,
            }
        },
    }).encode()

    req = urllib.request.Request(
        _INNERTUBE_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": client_ctx.get("userAgent", "Mozilla/5.0"),
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.youtube.com",
            "Referer": "https://www.youtube.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _lang_label(code: str) -> str:
    """Return a human-readable language label from a BCP-47 code."""
    base = code.split("-")[0].lower()
    return _LANGUAGE_NAMES.get(base, code.upper())


def _parse_audio_tracks(player_response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract audio-only formats with audioTrack metadata from a player response."""
    streaming = player_response.get("streamingData") or {}
    adaptive = streaming.get("adaptiveFormats") or []

    tracks: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for fmt in adaptive:
        mime = fmt.get("mimeType") or ""
        # Only audio-only streams
        if not mime.startswith("audio/"):
            continue

        audio_track = fmt.get("audioTrack") or {}
        display_name: str = audio_track.get("displayName") or ""
        track_id: str = audio_track.get("id") or ""
        # audioIsDefault = True means it is the original/primary language
        is_default: bool = audio_track.get("audioIsDefault", False)
        is_dubbed: bool = bool(audio_track) and not is_default
        is_auto_dubbed: bool = audio_track.get("isAutoDubbed", False)

        # Language code from track id (e.g. "en.4" -> "en")
        lang_code = track_id.split(".")[0] if track_id else ""
        itag = str(fmt.get("itag") or "")

        if not itag:
            continue

        # Skip DRM-protected streams (no URL available anyway)
        if fmt.get("drmFamilies"):
            continue

        # Determine container & codec from mimeType
        # e.g. 'audio/webm; codecs="opus"' or 'audio/mp4; codecs="mp4a.40.2"'
        ext = "webm" if "webm" in mime else "m4a"
        codec_raw = ""
        if 'codecs="' in mime:
            codec_raw = mime.split('codecs="')[1].split('"')[0]
        codec = codec_raw.split(".")[0] if codec_raw else ext

        abr_bps = fmt.get("averageBitrate") or fmt.get("bitrate") or 0
        abr_kbps = round(abr_bps / 1000) if abr_bps else None

        # Dedup by (lang+display, quality-tier)
        dedup_key = (
            lang_code or display_name or itag,
            str(abr_kbps or 0),
        )
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Build a human-readable label (same style as yt-dlp format notes)
        parts: list[str] = []

        if display_name:
            # YouTube provides a nice display name like "English (Original)"
            parts.append(display_name)
        elif lang_code:
            lbl = _lang_label(lang_code)
            if is_default:
                lbl += " (original)"
            elif is_auto_dubbed:
                lbl += " (auto-dubbed)"
            elif is_dubbed:
                lbl += " (dubbed)"
            parts.append(lbl)
        else:
            parts.append("Audio")

        # Container & codec
        if ext and codec and codec != ext:
            parts.append(f"{ext} ({codec})")
        elif ext:
            parts.append(ext)

        if abr_kbps:
            parts.append(f"{abr_kbps} kbps")

        parts.append(f"[id: {itag}]")
        label = " \u00b7 ".join(parts)   # middle dot separator

        tracks.append({
            "format_id": itag,
            "language": lang_code,
            "display_name": display_name,
            "label": label,
            "abr": abr_kbps,
            "ext": ext,
            "acodec": codec_raw or codec,
            "note": display_name,
            "is_default": is_default,
            "is_dubbed": is_dubbed,
            "is_auto_dubbed": is_auto_dubbed,
            "_source": "innertube",
        })

    # Sort: original/default first, dubbed next, auto-dubbed last; then by lang name
    def _sort_key(t: dict[str, Any]) -> tuple[int, str, float]:
        order = 0 if t.get("is_default") else (2 if t.get("is_auto_dubbed") else 1)
        lang = t.get("language") or ""
        abr = -(t.get("abr") or 0)
        return (order, lang, abr)

    tracks.sort(key=_sort_key)
    return tracks


def fetch_audio_tracks(url: str, proxy: str | None = None) -> list[dict[str, Any]]:
    """Return all audio tracks for *url* via InnerTube direct API call.

    Falls back gracefully: returns an empty list if the video is not a YouTube
    URL, the request times out, or the response contains no useful data.
    Tries multiple InnerTube clients until multi-language dub tracks are found.
    """
    video_id = _video_id(url)
    if not video_id:
        logger.debug("innertube: not a YouTube URL, skipping: %s", url)
        return []

    last_tracks: list[dict[str, Any]] = []

    for client_ctx in _INNERTUBE_CLIENTS:
        client_name = client_ctx.get("clientName", "?")
        try:
            logger.debug("innertube: trying client %s for %s", client_name, video_id)
            response = _innertube_request(video_id, client_ctx)
            tracks = _parse_audio_tracks(response)
            if tracks:
                last_tracks = tracks
                # If we see more than one unique language we have found dubs
                langs = {t["language"] for t in tracks if t["language"]}
                if len(langs) > 1:
                    logger.info(
                        "innertube: client %s found %d audio tracks (%d languages): %s",
                        client_name,
                        len(tracks),
                        len(langs),
                        langs,
                    )
                    return tracks
                logger.debug(
                    "innertube: client %s: %d tracks but only 1 language – trying next client",
                    client_name,
                    len(tracks),
                )
        except Exception as exc:
            logger.debug("innertube: client %s failed: %s", client_name, exc)

    if last_tracks:
        logger.info(
            "innertube: no multi-language dubs found; returning %d single-lang tracks",
            len(last_tracks),
        )
    else:
        logger.debug("innertube: no audio tracks found for video_id=%s", video_id)

    return last_tracks
