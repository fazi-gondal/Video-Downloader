"""Media metadata models mapped from yt-dlp info dicts."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class StreamType(StrEnum):
    VIDEO_ONLY = "video"
    AUDIO_ONLY = "audio"
    MUXED = "muxed"


def _classify_stream(f: dict[str, Any]) -> StreamType:
    """Classify a format dict.

    yt-dlp convention: codec == "none" means the stream is absent; codec is
    None when unknown (common in HLS/progressive formats that DO carry both).
    """
    vcodec = f.get("vcodec")
    acodec = f.get("acodec")
    has_height = f.get("height") is not None or (
        f.get("resolution") not in (None, "audio only")
    )
    if vcodec == "none":
        return StreamType.AUDIO_ONLY
    if acodec == "none":
        return StreamType.VIDEO_ONLY
    if vcodec is not None or has_height:
        return StreamType.MUXED
    return StreamType.AUDIO_ONLY


@dataclass(slots=True)
class FormatInfo:
    """One downloadable format as reported by yt-dlp."""

    format_id: str
    ext: str
    resolution: str | None
    height: int | None
    fps: float | None
    vcodec: str | None
    acodec: str | None
    tbr: float | None  # total bitrate (kbps)
    abr: float | None  # audio bitrate (kbps)
    filesize: int | None
    filesize_is_approx: bool
    stream_type: StreamType
    format_note: str | None = None

    @classmethod
    def from_ytdlp(cls, f: dict[str, Any]) -> FormatInfo:
        vcodec = f.get("vcodec")
        acodec = f.get("acodec")
        stream_type = _classify_stream(f)
        has_video = stream_type is not StreamType.AUDIO_ONLY
        has_audio = stream_type is not StreamType.VIDEO_ONLY

        filesize = f.get("filesize")
        filesize_is_approx = False
        if filesize is None and f.get("filesize_approx") is not None:
            filesize = f.get("filesize_approx")
            filesize_is_approx = True

        return cls(
            format_id=str(f.get("format_id", "")),
            ext=f.get("ext") or "",
            resolution=f.get("resolution"),
            height=f.get("height"),
            fps=f.get("fps"),
            vcodec=vcodec if has_video else None,
            acodec=acodec if has_audio else None,
            tbr=f.get("tbr"),
            abr=f.get("abr"),
            filesize=filesize,
            filesize_is_approx=filesize_is_approx,
            stream_type=stream_type,
            format_note=f.get("format_note"),
        )


@dataclass(slots=True)
class MediaInfo:
    """A single analyzed video."""

    url: str
    id: str
    title: str
    uploader: str | None
    duration: float | None  # seconds
    thumbnail_url: str | None
    webpage_url: str
    formats: list[FormatInfo] = field(default_factory=list)
    subtitles: dict[str, str] = field(default_factory=dict)
    audio_tracks: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_ytdlp(cls, info: dict[str, Any]) -> MediaInfo:
        subtitles: dict[str, str] = {}
        for code, entries in (info.get("subtitles") or {}).items():
            name = entries[0].get("name") if entries else code
            subtitles[str(code)] = str(name or code)

        for code, entries in (info.get("automatic_captions") or {}).items():
            if str(code) not in subtitles:
                name = entries[0].get("name") if entries else code
                subtitles[str(code)] = f"{name or code} (auto)"

        # Collect audio streams, keeping the highest quality stream per track.
        # Prefer Opus (webm) streams when available; fall back to AAC/other formats.
        _COMMON_LANG_NAMES: dict[str, str] = {
            "en": "English", "de": "German", "fr": "French", "es": "Spanish",
            "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese",
            "ko": "Korean", "zh": "Chinese", "zh-Hans": "Chinese (Simplified)",
            "zh-Hant": "Chinese (Traditional)", "hi": "Hindi", "ar": "Arabic",
            "bn": "Bangla", "tr": "Turkish", "pl": "Polish", "vi": "Vietnamese",
            "id": "Indonesian", "th": "Thai", "ta": "Tamil", "te": "Telugu",
            "ml": "Malayalam", "ur": "Urdu", "nl": "Dutch", "sv": "Swedish",
            "no": "Norwegian", "da": "Danish", "fi": "Finnish", "cs": "Czech",
            "el": "Greek", "he": "Hebrew", "hu": "Hungarian", "ro": "Romanian",
            "uk": "Ukrainian",
        }

        def _clean_track_name(l_code: str, f_note: str, l_name: str) -> str:
            clean = re.sub(r',\s*(low|medium|high|ultralow|drc|DRC)\b', '', f_note, flags=re.I).strip()
            if 'original (default)' in clean.lower():
                clean = re.sub(r'original\s*\(default\)', '(Original)', clean, flags=re.I).strip()
            elif clean.lower() in ('original', 'default'):
                clean = 'Original Audio'
            if clean and clean.lower() not in ('low', 'medium', 'high', 'drc'):
                return clean
            if l_name:
                return l_name
            return _COMMON_LANG_NAMES.get(l_code, l_code or "Audio")

        _track_best: dict[str, dict[str, Any]] = {}

        for f in info.get("formats") or []:
            if not (_classify_stream(f) == StreamType.AUDIO_ONLY or f.get("resolution") == "audio only"):
                continue

            fid = str(f.get("format_id", ""))
            if not fid:
                continue

            ext = f.get("ext") or ""
            if ext == "mhtml":
                continue

            acodec = f.get("acodec") or ""
            acodec_base = acodec.split(".")[0].lower() if acodec and acodec != "none" else ""
            is_opus = (ext == "webm") or (acodec_base == "opus")

            lang = str(f.get("language") or f.get("language_preference") or "")
            note = f.get("format_note") or ""
            lang_name = f.get("language_name") or ""
            track_name = _clean_track_name(lang, note, lang_name)

            track_key = f"{lang}_{track_name}" if (lang and track_name) else (lang or track_name or fid)
            abr = float(f.get("abr") or f.get("tbr") or 0.0)

            existing = _track_best.get(track_key)
            if existing is None:
                replace = True
            else:
                existing_is_opus = existing.get("is_opus", False)
                existing_abr = float(existing.get("abr") or 0.0)
                if is_opus and not existing_is_opus:
                    replace = True
                elif is_opus == existing_is_opus and abr > existing_abr:
                    replace = True
                else:
                    replace = False

            if replace:
                _track_best[track_key] = {
                    "_raw": f,
                    "format_id": fid,
                    "language": lang,
                    "track_name": track_name,
                    "abr": abr,
                    "ext": ext,
                    "acodec": acodec,
                    "note": note,
                    "is_opus": is_opus,
                    "asr": f.get("asr"),
                    "audio_channels": f.get("audio_channels"),
                    "lang_name": lang_name,
                }

        audio_tracks: list[dict[str, Any]] = []
        for track_key, best in _track_best.items():
            fid = best["format_id"]
            lang = best["language"]
            track_name = best["track_name"]
            note = best["note"]
            ext = best["ext"]
            acodec = best["acodec"]
            abr = best["abr"]
            asr = best["asr"]
            channels = best["audio_channels"]
            acodec_base = acodec.split(".")[0] if acodec and acodec != "none" else ext

            parts: list[str] = [track_name]

            # 2. Container & codec
            if ext and acodec_base and acodec_base != ext:
                parts.append(f"{ext} ({acodec_base})")
            elif ext:
                parts.append(ext)

            # 3. Quality metrics
            if abr:
                parts.append(f"{int(abr)} kbps")
            if channels and channels > 2:
                parts.append(f"{channels}ch")
            if asr:
                parts.append(f"{asr // 1000}kHz" if asr >= 1000 else f"{asr}Hz")

            # 4. Format ID
            parts.append(f"[id: {fid}]")

            label = " · ".join(parts)

            audio_tracks.append({
                "format_id": fid,
                "language": lang,
                "label": label,
                "abr": abr,
                "ext": ext,
                "acodec": acodec,
                "note": note,
            })

        # Sort: original/named languages first (by language code), then descending bitrate
        def _track_sort_key(t: dict[str, Any]) -> tuple[int, str, float]:
            l = t.get("language") or ""
            a = float(t.get("abr") or 0.0)
            return (0 if l else 1, l, -a)

        audio_tracks.sort(key=_track_sort_key)

        return cls(
            url=info.get("original_url") or info.get("webpage_url") or "",
            id=str(info.get("id", "")),
            title=info.get("title") or "(untitled)",
            uploader=info.get("uploader") or info.get("channel"),
            duration=info.get("duration"),
            thumbnail_url=info.get("thumbnail"),
            webpage_url=info.get("webpage_url") or info.get("original_url") or "",
            formats=[FormatInfo.from_ytdlp(f) for f in info.get("formats") or []],
            subtitles=subtitles,
            audio_tracks=audio_tracks,
        )


@dataclass(slots=True)
class PlaylistEntry:
    """One entry from a flat playlist extraction (no formats available)."""

    index: int
    id: str
    url: str
    title: str
    duration: float | None
    uploader: str | None = None

    @classmethod
    def from_ytdlp(cls, index: int, entry: dict[str, Any]) -> PlaylistEntry:
        return cls(
            index=index,
            id=str(entry.get("id", "")),
            url=entry.get("url") or entry.get("webpage_url") or "",
            title=entry.get("title") or f"Item {index}",
            duration=entry.get("duration"),
            uploader=entry.get("uploader") or entry.get("channel"),
        )


@dataclass(slots=True)
class PlaylistInfo:
    """An analyzed playlist/channel/collection."""

    url: str
    id: str
    title: str
    uploader: str | None
    thumbnail_url: str | None
    entries: list[PlaylistEntry] = field(default_factory=list)

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @classmethod
    def from_ytdlp(cls, info: dict[str, Any]) -> PlaylistInfo:
        entries = [
            PlaylistEntry.from_ytdlp(i, entry)
            for i, entry in enumerate(info.get("entries") or [], start=1)
            if entry
        ]
        thumbnail = info.get("thumbnail")
        if not thumbnail:
            thumbnails = info.get("thumbnails") or []
            thumbnail = thumbnails[-1].get("url") if thumbnails else None
        return cls(
            url=info.get("original_url") or info.get("webpage_url") or "",
            id=str(info.get("id", "")),
            title=info.get("title") or "(untitled playlist)",
            uploader=info.get("uploader") or info.get("channel"),
            thumbnail_url=thumbnail,
            entries=entries,
        )
