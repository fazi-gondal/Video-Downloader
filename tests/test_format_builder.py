"""Tests for the pure UI-choices -> yt-dlp options translation."""

from pathlib import Path

from video_downloader.config.settings import AppSettings
from video_downloader.models.download import DownloadMode, DownloadRequest
from video_downloader.services import format_builder as fb


def make_request(**overrides) -> DownloadRequest:
    defaults: dict = dict(
        url="https://www.youtube.com/watch?v=abc123",
        title="Test",
        mode=DownloadMode.VIDEO_AUDIO,
        output_dir=Path("/tmp/downloads"),
    )
    defaults.update(overrides)
    return DownloadRequest(**defaults)


class TestFormatSelector:
    def test_explicit_video_and_audio_ids(self):
        req = make_request(video_format_id="137", audio_format_id="140")
        assert fb.build_format_selector(req) == "137+140"

    def test_explicit_video_only(self):
        req = make_request(mode=DownloadMode.VIDEO_ONLY, video_format_id="137")
        assert fb.build_format_selector(req) == "137"

    def test_explicit_audio_only(self):
        req = make_request(mode=DownloadMode.AUDIO_ONLY, audio_format_id="251")
        assert fb.build_format_selector(req) == "251"

    def test_audio_preset(self):
        req = make_request(mode=DownloadMode.AUDIO_ONLY)
        assert fb.build_format_selector(req) == "ba/b"

    def test_video_audio_with_resolution_and_fps(self):
        req = make_request(max_height=1080, max_fps=60)
        expected = "bv*[height<=?1080][fps<=?60]+ba/b[height<=?1080][fps<=?60]/b"
        assert fb.build_format_selector(req) == expected

    def test_video_audio_best(self):
        req = make_request()
        assert fb.build_format_selector(req) == "bv*+ba/b"

    def test_video_audio_multi_audio(self):
        req = make_request(multi_audio=True)
        assert fb.build_format_selector(req) == "bv*+mergeall[vcodec=none]/b"

    def test_video_audio_selected_tracks(self):
        req = make_request(selected_audio_track_ids=("251-en", "251-es"))
        assert fb.build_format_selector(req) == "bv*+251-en+251-es"

    def test_video_only_with_resolution(self):
        req = make_request(mode=DownloadMode.VIDEO_ONLY, max_height=720)
        assert fb.build_format_selector(req) == "bv[height<=?720]/bv/b[height<=?720]/b"


class TestPostprocessors:
    def test_audio_extraction_with_bitrate(self):
        req = make_request(
            mode=DownloadMode.AUDIO_ONLY, audio_format="mp3", audio_bitrate_kbps=192
        )
        pps = fb.build_postprocessors(req)
        assert pps[0]["key"] == "FFmpegExtractAudio"
        assert pps[0]["preferredcodec"] == "mp3"
        assert pps[0]["preferredquality"] == "192"

    def test_lossless_audio_ignores_bitrate(self):
        req = make_request(
            mode=DownloadMode.AUDIO_ONLY, audio_format="flac", audio_bitrate_kbps=192
        )
        pps = fb.build_postprocessors(req)
        assert "preferredquality" not in pps[0]

    def test_video_remuxer_for_container(self):
        req = make_request(container="mkv")
        pps = fb.build_postprocessors(req)
        assert pps[0] == {"key": "FFmpegVideoRemuxer", "preferedformat": "mkv"}

    def test_thumbnail_skipped_for_matroska_without_ffprobe(self):
        # EmbedThumbnail on mkv calls ffprobe fatally; without it, skip the PP
        req = make_request(container="mkv", embed_thumbnail=True)
        keys = [pp["key"] for pp in fb.build_postprocessors(req, have_ffprobe=False)]
        assert "EmbedThumbnail" not in keys
        keys = [pp["key"] for pp in fb.build_postprocessors(req, have_ffprobe=True)]
        assert "EmbedThumbnail" in keys

    def test_thumbnail_kept_for_mp4_without_ffprobe(self):
        # mutagen handles mp4/m4a embedding, no ffprobe involved
        req = make_request(container="mp4", embed_thumbnail=True)
        keys = [pp["key"] for pp in fb.build_postprocessors(req, have_ffprobe=False)]
        assert "EmbedThumbnail" in keys

    def test_metadata_and_thumbnail_come_after_converters(self):
        req = make_request(
            mode=DownloadMode.AUDIO_ONLY,
            audio_format="mp3",
            embed_metadata=True,
            embed_thumbnail=True,
        )
        keys = [pp["key"] for pp in fb.build_postprocessors(req)]
        assert keys == ["FFmpegExtractAudio", "FFmpegMetadata", "EmbedThumbnail"]

    def test_subtitles_embedding_postprocessor(self):
        req = make_request(
            mode=DownloadMode.VIDEO_AUDIO,
            container="mkv",
            write_subtitles=True,
            embed_metadata=True,
        )
        keys = [pp["key"] for pp in fb.build_postprocessors(req)]
        assert keys == ["FFmpegVideoRemuxer", "FFmpegEmbedSubtitle", "FFmpegMetadata"]

    def test_subtitles_skipped_in_audio_only(self):
        req = make_request(
            mode=DownloadMode.AUDIO_ONLY,
            audio_format="mp3",
            write_subtitles=True,
        )
        keys = [pp["key"] for pp in fb.build_postprocessors(req)]
        assert "FFmpegEmbedSubtitle" not in keys


class TestYdlOpts:
    def test_basic_opts(self):
        req = make_request(container="mp4")
        opts = fb.build_ydl_opts(req, AppSettings(), "/usr/bin/ffmpeg")
        assert opts["format"] == "bv*+ba/b"
        assert opts["merge_output_format"] == "mp4"
        assert opts["ffmpeg_location"] == "/usr/bin/ffmpeg"
        assert opts["continuedl"] is True
        assert opts["quiet"] is True
        assert opts["noplaylist"] is True

    def test_settings_applied(self):
        settings = AppSettings(
            proxy="http://localhost:8080",
            cookies_browser="firefox",
            custom_headers={"X-Test": "1"},
            rate_limit_kbps=500,
        )
        opts = fb.build_ydl_opts(make_request(), settings, None)
        assert opts["proxy"] == "http://localhost:8080"
        assert opts["cookiesfrombrowser"] == ("firefox",)
        assert opts["http_headers"] == {"X-Test": "1"}
        assert opts["ratelimit"] == 500 * 1024
        assert "ffmpeg_location" not in opts

    def test_subtitles_and_thumbnail(self):
        req = make_request(write_subtitles=True, embed_thumbnail=True)
        opts = fb.build_ydl_opts(req, AppSettings(), None)
        assert opts["writesubtitles"] is True
        assert opts["writeautomaticsub"] is True
        assert opts["subtitleslangs"] == ["all"]
        assert opts["writethumbnail"] is True

    def test_custom_subtitles_langs(self):
        req = make_request(write_subtitles=True, subtitle_langs=("en", "es"))
        opts = fb.build_ydl_opts(req, AppSettings(), None)
        assert opts["subtitleslangs"] == ["en", "es"]

    def test_multi_audio_opts(self):
        req = make_request(multi_audio=True)
        opts = fb.build_ydl_opts(req, AppSettings(), None)
        assert opts["audio_multistreams"] is True

    def test_selected_audio_multistreams_opts(self):
        req = make_request(selected_audio_track_ids=("251-en", "251-es"))
        opts = fb.build_ydl_opts(req, AppSettings(), None)
        assert opts["audio_multistreams"] is True

    def test_playlist_output_template(self):
        req = make_request(playlist_title="Mi lista", playlist_index=3)
        opts = fb.build_ydl_opts(req, AppSettings(), None)
        assert "%(playlist_index)03d" in opts["outtmpl"]

    def test_analysis_opts_flat(self):
        opts = fb.build_analysis_opts(AppSettings())
        assert opts["extract_flat"] == "in_playlist"
        assert opts["skip_download"] is True

    def test_analysis_opts_fail_fast(self):
        # Interactive analysis must not inherit yt-dlp's long retry chains:
        # offline failures should surface in seconds, not minutes.
        opts = fb.build_analysis_opts(AppSettings())
        assert opts["socket_timeout"] <= 15
        assert opts["retries"] <= 3
        assert opts["extractor_retries"] <= 1

    def test_youtube_js_challenge_support(self):
        # Both option sets must allow the EJS solver (yt-dlp-ejs + runtime)
        for opts in (
            fb.build_ydl_opts(make_request(), AppSettings(), None),
            fb.build_analysis_opts(AppSettings()),
        ):
            assert opts["remote_components"] == ["ejs:github"]
            assert "deno" in opts["js_runtimes"]

    def test_opts_accepted_by_yt_dlp(self):
        import yt_dlp

        opts = fb.build_ydl_opts(make_request(), AppSettings(), None)
        with yt_dlp.YoutubeDL(opts) as ydl:  # raises on invalid params
            assert ydl.params["remote_components"] == {"ejs:github"}
            # Force runtime initialization: yt-dlp does config.get('path'),
            # so every runtime config must be a dict (never None)
            runtimes = ydl._js_runtimes
            assert "deno" in runtimes
