"""Environment helper tests."""

from pathlib import Path
from unittest import mock

from video_downloader.utils.env import find_executable, find_js_runtime


def test_find_executable_prefers_bundled_deno(tmp_path: Path):
    deno = tmp_path / "deno.exe"
    deno.write_text("", encoding="utf-8")

    with mock.patch(
        "video_downloader.utils.env.find_bundled_tool", return_value=deno
    ), mock.patch("shutil.which", return_value="/usr/bin/deno"):
        assert find_executable("deno") == deno
        assert find_js_runtime() == ("deno", deno)


def test_find_executable_falls_back_to_path():
    with mock.patch(
        "video_downloader.utils.env.find_bundled_tool", return_value=None
    ), mock.patch("shutil.which", return_value="/usr/bin/deno"):
        assert find_executable("deno") == Path("/usr/bin/deno")
