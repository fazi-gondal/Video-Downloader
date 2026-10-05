"""Tests for ARY Plus custom extractors."""

from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import ExtractorError

from video_downloader.services.extractors.aryplus import AryPlusIE, AryPlusSeriesIE


def test_aryplus_video_valid_url_matching():
    valid_urls = [
        "https://aryplus.tv/video/v2/3/6a6e0b1e9bc4b079859bc14b/6a57868b5bf57c474cc00a50",
        "http://www.aryplus.tv/video/v2/1/abc12345/def67890",
        "https://aryplus.tv/video/v2/2/dmvideoid123/seriesid456",
    ]
    for url in valid_urls:
        assert AryPlusIE.suitable(url) is True

    invalid_urls = [
        "https://aryplus.tv/",
        "https://aryplus.tv/series/6a57868b5bf57c474cc00a50",
        "https://youtube.com/watch?v=123",
    ]
    for url in invalid_urls:
        assert AryPlusIE.suitable(url) is False


def test_aryplus_series_valid_url_matching():
    valid_urls = [
        "https://aryplus.tv/series/6a57868b5bf57c474cc00a50",
        "http://www.aryplus.tv/series/123456789abcdef0",
    ]
    for url in valid_urls:
        assert AryPlusSeriesIE.suitable(url) is True

    invalid_urls = [
        "https://aryplus.tv/video/v2/3/6a6e0b1e9bc4b079859bc14b/6a57868b5bf57c474cc00a50",
        "https://aryplus.tv/",
    ]
    for url in invalid_urls:
        assert AryPlusSeriesIE.suitable(url) is False


def test_aryplus_delegates_to_youtube():
    ie = AryPlusIE(MagicMock())
    result = ie._real_extract("https://aryplus.tv/video/v2/1/dQw4w9WgXcQ/series123")
    assert result["_type"] == "url"
    assert result["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert result["ie_key"] == "Youtube"


def test_aryplus_delegates_to_dailymotion():
    ie = AryPlusIE(MagicMock())
    result = ie._real_extract("https://aryplus.tv/video/v2/2/x7zabc/series123")
    assert result["_type"] == "url"
    assert result["url"] == "https://www.dailymotion.com/video/x7zabc"
    assert result["ie_key"] == "Dailymotion"


def test_aryplus_custom_cdn_extraction():
    ie = AryPlusIE(MagicMock())

    def fake_call_api(endpoint, video_id, **kwargs):
        if "api/cdn/ep/" in endpoint:
            return {
                "episode": {
                    "_id": "6a6e0b1e9bc4b079859bc14b",
                    "title": "Episode 1",
                    "description": "Episode 1 description",
                    "videoSource": "https://vod.aryzap.com/test/adp.10.m3u8",
                    "imagePath": "cdnv1/test.webp",
                    "videoLength": "1800",
                    "videoEpNumber": 1,
                    "drmEnabled": False,
                }
            }
        if "api/series/" in endpoint:
            return {"title": "Drama Title"}
        return {}

    with (
        patch.object(ie, "_call_api", side_effect=fake_call_api),
        patch.object(
            ie,
            "_extract_m3u8_formats",
            return_value=[
                {"format_id": "720", "resolution": "1280x720", "height": 720, "ext": "mp4"}
            ],
        ),
    ):
        result = ie._real_extract(
            "https://aryplus.tv/video/v2/3/6a6e0b1e9bc4b079859bc14b/6a57868b5bf57c474cc00a50"
        )
        assert result["id"] == "6a6e0b1e9bc4b079859bc14b"
        assert result["title"] == "Drama Title - Episode 1"
        assert result["description"] == "Episode 1 description"
        assert result["duration"] == 1800
        assert result["episode_number"] == 1
        assert result["thumbnail"] == "https://images.aryplus.tv/cdnv1/test.webp"
        assert len(result["formats"]) == 1


def test_aryplus_drm_protected_raises_error():
    ie = AryPlusIE(MagicMock())

    def fake_call_api(endpoint, video_id, **kwargs):
        return {
            "episode": {
                "_id": "drm123",
                "title": "DRM Episode",
                "videoSource": "https://vod.aryzap.com/drm.m3u8",
                "drmEnabled": True,
            }
        }

    with patch.object(ie, "_call_api", side_effect=fake_call_api):
        with pytest.raises(ExtractorError, match="DRM protected"):
            ie._real_extract("https://aryplus.tv/video/v2/3/drm123/series123")


def test_aryplus_series_playlist_extraction():
    ie = AryPlusSeriesIE(MagicMock())

    def fake_call_api(endpoint, series_id, **kwargs):
        if "api/series/" in endpoint:
            return {"title": "Full Drama Series"}
        if "api/v2/cdn/pg/" in endpoint:
            query = kwargs.get("query") or {}
            page = query.get("page", 1)
            if page == 1:
                return {
                    "totalPages": 2,
                    "episode": [
                        {"_id": "ep1", "title": "Episode 1", "videoEpNumber": 1},
                        {"_id": "ep2", "title": "Episode 2", "videoEpNumber": 2},
                    ],
                }
            if page == 2:
                return {
                    "totalPages": 2,
                    "episode": [
                        {"_id": "ep3", "title": "Episode 3", "videoEpNumber": 3},
                    ],
                }
        return {}

    with patch.object(ie, "_call_api", side_effect=fake_call_api):
        result = ie._real_extract("https://aryplus.tv/series/series12345")
        assert result["_type"] == "playlist"
        assert result["id"] == "series12345"
        assert result["title"] == "Full Drama Series"
        entries = list(result["entries"])
        assert len(entries) == 3
        assert entries[0]["id"] == "ep1"
        assert entries[0]["title"] == "Full Drama Series - Episode 1"
        assert entries[2]["id"] == "ep3"
