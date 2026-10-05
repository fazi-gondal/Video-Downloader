"""Custom yt-dlp extractors for ARY Plus (aryplus.tv)."""

from __future__ import annotations

import contextlib
import logging
from typing import Any

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError

logger = logging.getLogger(__name__)


class AryPlusBaseIE(InfoExtractor):
    """Base extractor providing ARY Plus API client configuration."""

    _API_BASE = "https://be.aryplus.tv"
    _API_KEY = "ak_37515186786306625012043079404171"

    def _call_api(
        self,
        endpoint: str,
        video_id: str,
        *,
        note: str = "Downloading API JSON",
        fatal: bool = True,
        query: dict[str, Any] | None = None,
    ) -> Any:
        headers = {
            "x-api-key": self._API_KEY,
            "Referer": "https://aryplus.tv/",
            "Origin": "https://aryplus.tv",
        }
        url = f"{self._API_BASE}/{endpoint.lstrip('/')}"
        return self._download_json(
            url,
            video_id,
            note=note,
            fatal=fatal,
            headers=headers,
            query=query,
        )


class AryPlusIE(AryPlusBaseIE):
    """Extractor for ARY Plus video episodes."""

    IE_NAME = "aryplus"
    IE_DESC = "ARY Plus (aryplus.tv) video extractor"
    _VALID_URL = r"https?://(?:www\.)?aryplus\.tv/video/v2/(?P<platformid>\d+)/(?P<videoid>[\w]+)/(?P<seriesid>[\w]+)"

    _TESTS = [
        {
            "url": "https://aryplus.tv/video/v2/3/6a6e0b1e9bc4b079859bc14b/6a57868b5bf57c474cc00a50",
            "info_dict": {
                "id": "6a6e0b1e9bc4b079859bc14b",
                "ext": "mp4",
                "title": "Dar-E-Nijaat - Episode 1",
                "description": "md5:2995cece7a7b8e51147a4659b407a16e",
                "duration": 2273,
                "episode_number": 1,
                "series": "Dar-E-Nijaat",
            },
            "params": {"skip_download": True},
        }
    ]

    def _real_extract(self, url: str) -> dict[str, Any]:
        mobj = self._match_valid_url(url)
        assert mobj is not None
        platform_id = mobj.group("platformid")
        video_id = mobj.group("videoid")
        series_id = mobj.group("seriesid")

        # Platform 1: YouTube
        if platform_id == "1":
            return self.url_result(f"https://www.youtube.com/watch?v={video_id}", ie="Youtube")

        # Platform 2: Dailymotion
        if platform_id == "2":
            dm_url = f"https://www.dailymotion.com/video/{video_id}"
            return self.url_result(dm_url, ie="Dailymotion")

        # Platform 3: ARY Custom CDN
        data = self._call_api(
            f"api/cdn/ep/{video_id}",
            video_id,
            note="Downloading episode metadata",
        )
        episode = data.get("episode") if isinstance(data, dict) else None
        if isinstance(episode, list):
            episode = episode[0] if episode else None
        if not isinstance(episode, dict):
            raise ExtractorError(f"Episode data not found for ID: {video_id}", expected=True)

        if episode.get("drmEnabled"):
            raise ExtractorError(
                "This video is DRM protected and cannot be downloaded",
                expected=True,
            )

        video_source = episode.get("videoSource")
        if not video_source:
            raise ExtractorError("No video source stream found in episode response", expected=True)

        formats = self._extract_m3u8_formats(
            video_source,
            video_id,
            ext="mp4",
            entry_protocol="m3u8_native",
        )

        series_title: str | None = None
        if series_id:
            try:
                series_data = self._call_api(
                    f"api/series/{series_id}",
                    video_id,
                    note="Downloading series metadata",
                    fatal=False,
                )
                if isinstance(series_data, dict):
                    series_title = series_data.get("title")
            except Exception:
                pass

        ep_title = episode.get("title") or f"Episode {episode.get('videoEpNumber') or video_id}"
        full_title = f"{series_title} - {ep_title}" if series_title else ep_title

        thumbnail: str | None = None
        image_path = episode.get("imagePathV2") or episode.get("imagePath")
        if image_path:
            thumbnail = f"https://images.aryplus.tv/{str(image_path).lstrip('/')}"

        duration_val = episode.get("videoLength")
        duration = None
        if duration_val:
            with contextlib.suppress(ValueError, TypeError):
                duration = int(float(duration_val))

        ep_number_val = episode.get("videoEpNumber")
        ep_number = None
        if ep_number_val is not None:
            with contextlib.suppress(ValueError, TypeError):
                ep_number = int(ep_number_val)

        return {
            "id": video_id,
            "title": full_title,
            "description": episode.get("description"),
            "formats": formats,
            "thumbnail": thumbnail,
            "duration": duration,
            "episode_number": ep_number,
            "series": series_title,
            "webpage_url": url,
        }


class AryPlusSeriesIE(AryPlusBaseIE):
    """Extractor for ARY Plus series / drama playlists."""

    IE_NAME = "aryplus:series"
    IE_DESC = "ARY Plus (aryplus.tv) series playlist extractor"
    _VALID_URL = r"https?://(?:www\.)?aryplus\.tv/series/(?P<id>[\w]+)"

    def _real_extract(self, url: str) -> dict[str, Any]:
        series_id = self._match_id(url)
        series_data = (
            self._call_api(
                f"api/series/{series_id}",
                series_id,
                note="Downloading series metadata",
                fatal=False,
            )
            or {}
        )
        series_title = series_data.get("title") if isinstance(series_data, dict) else None
        title = series_title or series_id

        entries = []
        page = 1
        while True:
            data = self._call_api(
                f"api/v2/cdn/pg/{series_id}",
                series_id,
                note=f"Downloading series episode list page {page}",
                query={"page": page, "limit": 50},
                fatal=False,
            )
            if not isinstance(data, dict):
                break
            episodes = data.get("episode") or []
            if not episodes or not isinstance(episodes, list):
                break

            for ep in episodes:
                if not isinstance(ep, dict):
                    continue
                ep_id = ep.get("_id")
                if not ep_id:
                    continue
                ep_title = ep.get("title") or f"Episode {ep.get('videoEpNumber') or ep_id}"
                entry_title = f"{series_title} - {ep_title}" if series_title else ep_title
                entries.append(
                    self.url_result(
                        f"https://aryplus.tv/video/v2/3/{ep_id}/{series_id}",
                        ie=AryPlusIE.ie_key(),
                        video_id=ep_id,
                        video_title=entry_title,
                    )
                )

            total_pages = data.get("totalPages")
            if not total_pages or page >= total_pages:
                break
            page += 1

        return self.playlist_result(entries, playlist_id=series_id, playlist_title=title)
