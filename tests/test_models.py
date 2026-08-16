"""Tests for yt-dlp info dict -> model parsing."""

from video_downloader.models.media import (
    FormatInfo,
    MediaInfo,
    PlaylistInfo,
    StreamType,
)


class TestFormatInfo:
    def test_muxed_format(self):
        f = FormatInfo.from_ytdlp(
            {
                "format_id": "22",
                "ext": "mp4",
                "resolution": "1280x720",
                "height": 720,
                "fps": 30,
                "vcodec": "avc1.64001F",
                "acodec": "mp4a.40.2",
                "tbr": 1200.5,
                "filesize": 10_000_000,
            }
        )
        assert f.stream_type is StreamType.MUXED
        assert f.filesize == 10_000_000
        assert not f.filesize_is_approx

    def test_video_only_with_approx_size(self):
        f = FormatInfo.from_ytdlp(
            {
                "format_id": "137",
                "ext": "mp4",
                "vcodec": "avc1",
                "acodec": "none",
                "filesize_approx": 55_000_000,
            }
        )
        assert f.stream_type is StreamType.VIDEO_ONLY
        assert f.acodec is None
        assert f.filesize == 55_000_000
        assert f.filesize_is_approx

    def test_progressive_with_unknown_codecs_is_muxed(self):
        # HLS/progressive formats often report vcodec/acodec as None (unknown)
        f = FormatInfo.from_ytdlp(
            {"format_id": "http-240p", "ext": "mp4", "resolution": "480x270"}
        )
        assert f.stream_type is StreamType.MUXED

    def test_hls_audio_with_unknown_codecs(self):
        f = FormatInfo.from_ytdlp(
            {"format_id": "hls-audio-low", "ext": "mp4", "resolution": "audio only"}
        )
        assert f.stream_type is StreamType.AUDIO_ONLY

    def test_audio_only_no_size(self):
        f = FormatInfo.from_ytdlp(
            {"format_id": "251", "ext": "webm", "vcodec": "none", "acodec": "opus", "abr": 160}
        )
        assert f.stream_type is StreamType.AUDIO_ONLY
        assert f.vcodec is None
        assert f.filesize is None


class TestMediaInfo:
    def test_from_ytdlp(self):
        info = MediaInfo.from_ytdlp(
            {
                "id": "abc",
                "title": "Video de prueba",
                "uploader": "Canal",
                "duration": 123.4,
                "thumbnail": "https://example.com/t.jpg",
                "webpage_url": "https://youtube.com/watch?v=abc",
                "formats": [
                    {"format_id": "22", "ext": "mp4", "vcodec": "avc1", "acodec": "aac"}
                ],
            }
        )
        assert info.title == "Video de prueba"
        assert len(info.formats) == 1

    def test_audio_tracks_parsing(self):
        info = MediaInfo.from_ytdlp(
            {
                "id": "test123",
                "title": "Multi Audio Video",
                "formats": [
                    {
                        "format_id": "251-en",
                        "ext": "webm",
                        "vcodec": "none",
                        "acodec": "opus",
                        "language": "en",
                        "format_note": "English original (default), medium",
                        "abr": 128.0,
                    },
                    {
                        "format_id": "251-de",
                        "ext": "webm",
                        "vcodec": "none",
                        "acodec": "opus",
                        "language": "de",
                        "format_note": "German, medium",
                        "abr": 128.0,
                    },
                    {
                        "format_id": "251-ja",
                        "ext": "webm",
                        "vcodec": "none",
                        "acodec": "opus",
                        "language": "ja",
                        "format_note": "Japanese, medium",
                        "abr": 128.0,
                    },
                ],
            }
        )
        assert len(info.audio_tracks) == 3
        labels = [t["label"] for t in info.audio_tracks]
        assert any("English (Original)" in l for l in labels)
        assert any("German" in l for l in labels)
        assert any("Japanese" in l for l in labels)

    def test_missing_fields(self):
        info = MediaInfo.from_ytdlp({"id": "x"})
        assert info.title == "(untitled)"
        assert info.duration is None
        assert info.formats == []


class TestPlaylistInfo:
    def test_from_flat_extraction(self):
        info = PlaylistInfo.from_ytdlp(
            {
                "_type": "playlist",
                "id": "PL1",
                "title": "Mi lista",
                "uploader": "Canal",
                "entries": [
                    {"id": "a", "url": "https://youtu.be/a", "title": "Uno", "duration": 10},
                    None,  # yt-dlp can yield None entries for unavailable videos
                    {"id": "b", "url": "https://youtu.be/b", "title": "Dos"},
                ],
            }
        )
        assert info.entry_count == 2
        assert info.entries[0].index == 1
        assert info.entries[1].title == "Dos"
