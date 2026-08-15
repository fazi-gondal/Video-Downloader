"""Formatting and validation helper tests."""

from video_downloader.utils.formatting import (
    human_bytes,
    human_duration,
    human_eta,
    human_speed,
)
from video_downloader.utils.validators import (
    is_valid_url,
    looks_like_playlist,
    sanitize_filename,
)


class TestFormatting:
    def test_bytes(self):
        assert human_bytes(None) == "desconocido"
        assert human_bytes(512) == "512 B"
        assert human_bytes(1536) == "1.5 KB"
        assert human_bytes(10_485_760) == "10.0 MB"
        assert human_bytes(10_485_760, approx=True) == "~10.0 MB"

    def test_speed(self):
        assert human_speed(None) == "—"
        assert human_speed(1_048_576) == "1.0 MB/s"

    def test_eta(self):
        assert human_eta(None) == "—"
        assert human_eta(75) == "1:15"
        assert human_eta(3725) == "1:02:05"

    def test_duration(self):
        assert human_duration(None) == "desconocido"
        assert human_duration(59) == "0:59"


class TestValidators:
    def test_valid_urls(self):
        assert is_valid_url("https://www.youtube.com/watch?v=abc")
        assert is_valid_url("http://youtu.be/abc")
        assert not is_valid_url("not a url")
        assert not is_valid_url("ftp://example.com/x")
        assert not is_valid_url("")

    def test_playlist_heuristic(self):
        assert looks_like_playlist("https://www.youtube.com/playlist?list=PL123")
        assert looks_like_playlist("https://www.youtube.com/watch?v=a&list=PL123")
        assert looks_like_playlist("https://www.youtube.com/@somechannel")
        assert not looks_like_playlist("https://www.youtube.com/watch?v=abc")

    def test_sanitize_filename(self):
        assert sanitize_filename('a/b\\c:d*e?f"g<h>i|j') == "a_b_c_d_e_f_g_h_i_j"
        assert sanitize_filename("  nombre.  ") == "nombre"
        assert sanitize_filename("") == "archivo"
