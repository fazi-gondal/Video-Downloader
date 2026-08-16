"""User settings model and JSON persistence."""

from __future__ import annotations

import dataclasses
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

import platformdirs

from video_downloader.config.constants import APP_AUTHOR, APP_NAME, DEFAULT_MAX_CONCURRENT
from video_downloader.utils.paths import default_download_dir

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AppSettings:
    download_dir: str = ""
    max_concurrent: int = DEFAULT_MAX_CONCURRENT
    proxy: str = ""
    cookies_browser: str = ""  # "" = disabled; else chrome/firefox/safari/...
    custom_headers: dict[str, str] = field(default_factory=dict)
    rate_limit_kbps: int = 0  # 0 = unlimited
    keep_originals: bool = True
    write_subtitles: bool = False
    subtitle_langs: list[str] = field(default_factory=lambda: ["all"])
    multi_audio: bool = False
    embed_thumbnail: bool = True
    embed_metadata: bool = True
    theme_mode: str = "system"  # system | light | dark

    def __post_init__(self) -> None:
        if not self.download_dir:
            self.download_dir = str(default_download_dir())

    @property
    def download_path(self) -> Path:
        return Path(self.download_dir).expanduser()


class SettingsRepository:
    """Loads/saves :class:`AppSettings` as JSON in the user config dir."""

    def __init__(self, config_file: Path | None = None) -> None:
        self._file = config_file or (
            Path(platformdirs.user_config_dir(APP_NAME, APP_AUTHOR)) / "settings.json"
        )

    @property
    def file(self) -> Path:
        return self._file

    def load(self) -> AppSettings:
        try:
            raw = json.loads(self._file.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return AppSettings()
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read settings (%s); using defaults", exc)
            return AppSettings()

        known = {f.name for f in dataclasses.fields(AppSettings)}
        filtered = {k: v for k, v in raw.items() if k in known}
        if filtered.get("subtitle_langs") == ["es", "en"]:
            filtered["subtitle_langs"] = ["all"]
        try:
            return AppSettings(**filtered)
        except (TypeError, ValueError) as exc:
            logger.warning("Invalid settings content (%s); using defaults", exc)
            return AppSettings()

    def save(self, settings: AppSettings) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(dataclasses.asdict(settings), indent=2, ensure_ascii=False)
        self._file.write_text(payload, encoding="utf-8")

    def export_to(self, target: Path, settings: AppSettings) -> None:
        target.write_text(
            json.dumps(dataclasses.asdict(settings), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def import_from(self, source: Path) -> AppSettings:
        raw = json.loads(source.read_text(encoding="utf-8"))
        known = {f.name for f in dataclasses.fields(AppSettings)}
        filtered = {k: v for k, v in raw.items() if k in known}
        settings = AppSettings(**filtered)
        self.save(settings)
        return settings
