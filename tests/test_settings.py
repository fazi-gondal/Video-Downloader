"""Settings persistence round-trip and recovery tests."""

from pathlib import Path

from video_downloader.config.settings import AppSettings, SettingsRepository


def test_defaults_have_download_dir():
    settings = AppSettings()
    assert settings.download_dir
    assert settings.max_concurrent >= 1


def test_round_trip(tmp_path: Path):
    repo = SettingsRepository(tmp_path / "settings.json")
    settings = AppSettings(
        download_dir="/tmp/videos",
        max_concurrent=4,
        proxy="http://proxy:1234",
        custom_headers={"X-A": "b"},
        theme_mode="dark",
    )
    repo.save(settings)
    loaded = repo.load()
    assert loaded == settings


def test_missing_file_returns_defaults(tmp_path: Path):
    repo = SettingsRepository(tmp_path / "nope.json")
    assert repo.load() == AppSettings()


def test_corrupt_file_returns_defaults(tmp_path: Path):
    file = tmp_path / "settings.json"
    file.write_text("{not json!!", encoding="utf-8")
    repo = SettingsRepository(file)
    assert repo.load() == AppSettings()


def test_unknown_keys_ignored(tmp_path: Path):
    file = tmp_path / "settings.json"
    file.write_text('{"max_concurrent": 3, "future_option": true}', encoding="utf-8")
    repo = SettingsRepository(file)
    assert repo.load().max_concurrent == 3


def test_export_import(tmp_path: Path):
    repo = SettingsRepository(tmp_path / "settings.json")
    settings = AppSettings(max_concurrent=5)
    exported = tmp_path / "export.json"
    repo.export_to(exported, settings)
    restored = repo.import_from(exported)
    assert restored.max_concurrent == 5
    assert repo.load().max_concurrent == 5
