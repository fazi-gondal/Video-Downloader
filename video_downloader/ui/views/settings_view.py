"""Settings: bento layout (form sections left, dependency status right)
with a fixed footer for save/export/import. Bound to the settings repository."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft

from video_downloader.config.constants import (
    COOKIE_BROWSERS,
    INSTALL_DENO_URL,
    INSTALL_FFMPEG_URL,
    MAX_CONCURRENT_FRAGMENTS,
    MAX_CONCURRENT_LIMIT,
)
from video_downloader.ui import theme
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.buttons import primary_button, secondary_button
from video_downloader.ui.components.surface import surface_card
from video_downloader.ui.components.toast import show_toast
from video_downloader.ui.texts import t
from video_downloader.ui.utils import safe_update
from video_downloader.utils.env import find_js_runtime

_THEME_OPTIONS: list[tuple[str, str, ft.IconData]] = [
    ("light", "theme_light", ft.Icons.LIGHT_MODE_OUTLINED),
    ("dark", "theme_dark", ft.Icons.DARK_MODE_OUTLINED),
    ("system", "theme_system", ft.Icons.DEVICES_OUTLINED),
]


def _status_card(
    title: str,
    detail: str,
    icon: ft.IconData,
    color: str,
    help_url: str | None = None,
) -> ft.Container:
    """Dependency status card. With `help_url` (dependency missing/partial)
    the card becomes clickable and deep-links to the install guide."""
    row_items: list[ft.Control] = [
        ft.Icon(icon, color=color, size=22),
        ft.Column(
            [
                ft.Text(
                    title,
                    weight=ft.FontWeight.W_600,
                    size=14,
                    color=ft.Colors.ON_SURFACE,
                ),
                ft.Text(detail, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            spacing=3,
            expand=True,
        ),
    ]
    if help_url:
        row_items.append(
            ft.Icon(ft.Icons.OPEN_IN_NEW, size=16, color=ft.Colors.ON_SURFACE_VARIANT)
        )
    card = surface_card(
        ft.Row(
            row_items,
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
        padding=14,
    )
    if help_url:
        card.url = help_url
        card.ink = True
        card.tooltip = t("install_guide_tooltip")
    return card


def _section(icon: ft.IconData, title: str, *controls: ft.Control) -> ft.Container:
    return surface_card(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(icon, size=18, color=ft.Colors.PRIMARY),
                        ft.Text(title, style=theme.headline_md()),
                    ],
                    spacing=10,
                ),
                *controls,
            ],
            spacing=14,
        ),
        padding=18,
    )


def _parse_headers(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" in line:
            name, _, value = line.partition(":")
            if name.strip() and value.strip():
                headers[name.strip()] = value.strip()
    return headers


class _ThemeSelector(ft.Row):
    """Three selectable cards: light / dark / system."""

    def __init__(self, value: str, on_change: Callable[[str], None]) -> None:
        super().__init__()
        self.value = value
        self._on_change = on_change
        self._cards: dict[str, ft.Container] = {}
        self._icons: dict[str, ft.Icon] = {}
        self.spacing = 10

        for key, label_key, icon in _THEME_OPTIONS:
            icon_ctl = ft.Icon(icon, size=22)
            card = ft.Container(
                content=ft.Column(
                    [
                        icon_ctl,
                        ft.Text(
                            t(label_key),
                            size=13,
                            weight=ft.FontWeight.W_500,
                            color=ft.Colors.ON_SURFACE,
                        ),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(vertical=14, horizontal=10),
                border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
                expand=True,
                alignment=ft.Alignment.CENTER,
                on_click=self._make_handler(key),
                ink=True,
            )
            self._cards[key] = card
            self._icons[key] = icon_ctl
            self.controls.append(card)
        self._style()

    def _make_handler(self, key: str):
        def handler(e: ft.Event) -> None:
            self.set_value(key)
            self._on_change(key)

        return handler

    def set_value(self, value: str) -> None:
        self.value = value
        self._style()
        safe_update(self)

    def _style(self) -> None:
        for key, card in self._cards.items():
            selected = key == self.value
            card.bgcolor = (
                ft.Colors.PRIMARY_CONTAINER if selected else ft.Colors.SURFACE_CONTAINER_LOWEST
            )
            card.border = ft.Border.all(
                1.5 if selected else 1,
                ft.Colors.PRIMARY if selected else ft.Colors.OUTLINE_VARIANT,
            )
            self._icons[key].color = (
                ft.Colors.PRIMARY if selected else ft.Colors.ON_SURFACE_VARIANT
            )


class SettingsView(ft.Column):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.expand = True
        self.spacing = 14
        settings = ctx.settings

        # --- Dependency status cards ----------------------------------------
        ffmpeg_card = self._build_ffmpeg_card()

        runtime = find_js_runtime()
        if runtime:
            name, path = runtime
            js_text = f"{name} · {path} — {t('js_runtime_found')}"
            js_icon, js_color = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN
            js_url = None
        else:
            js_text = t("js_runtime_missing")
            js_icon, js_color = ft.Icons.WARNING, ft.Colors.ORANGE
            js_url = INSTALL_DENO_URL
        js_card = _status_card(
            t("js_runtime_status"), js_text, js_icon, js_color, help_url=js_url
        )

        # --- Form fields ---------------------------------------------------
        from video_downloader.ui.components.folder_picker import FolderPicker

        self._theme_selector = _ThemeSelector(
            settings.theme_mode, on_change=self._on_theme_change
        )
        ctx.on_theme_change(self._sync_theme_selector)

        self._folder = FolderPicker(settings.download_path)

        self._concurrent_label = ft.Text(
            f"{t('max_concurrent')}: {settings.max_concurrent}",
            size=13.5,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.ON_SURFACE,
        )
        self._concurrent = ft.Slider(
            min=1,
            max=MAX_CONCURRENT_LIMIT,
            divisions=MAX_CONCURRENT_LIMIT - 1,
            value=settings.max_concurrent,
            on_change=self._on_concurrent_change,
        )
        self._fragments_label = ft.Text(
            f"{t('concurrent_fragments')}: {settings.concurrent_fragments}",
            size=13.5,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.ON_SURFACE,
        )
        self._fragments = ft.Slider(
            min=1,
            max=MAX_CONCURRENT_FRAGMENTS,
            divisions=MAX_CONCURRENT_FRAGMENTS - 1,
            value=settings.concurrent_fragments,
            on_change=self._on_fragments_change,
        )

        self._proxy = ft.TextField(label=t("proxy"), value=settings.proxy, expand=True)

        cookie_labels = [t("cookies_none") if b == "" else b for b in COOKIE_BROWSERS]
        self._cookies = ft.Dropdown(
            label=t("cookies_browser"),
            options=[
                ft.DropdownOption(key=browser, text=label)
                for browser, label in zip(COOKIE_BROWSERS, cookie_labels, strict=True)
            ],
            value=settings.cookies_browser,
            width=260,
        )

        self._headers = ft.TextField(
            label=t("custom_headers"),
            value="\n".join(f"{k}: {v}" for k, v in settings.custom_headers.items()),
            multiline=True,
            min_lines=2,
            max_lines=4,
            expand=True,
        )
        self._rate_limit = ft.TextField(
            label=t("rate_limit"),
            value=str(settings.rate_limit_kbps),
            width=260,
        )

        self._keep_originals = ft.Switch(
            label=t("keep_originals"), value=settings.keep_originals
        )
        self._subtitles = ft.Switch(
            label=t("subtitles"), value=settings.write_subtitles
        )
        self._subtitle_langs = ft.TextField(
            label=t("subtitle_langs"),
            hint_text=t("subtitle_langs_hint"),
            value=", ".join(settings.subtitle_langs),
            width=280,
        )
        self._multi_audio = ft.Switch(
            label=t("multi_audio"), value=settings.multi_audio
        )
        self._thumbnail = ft.Switch(
            label=t("embed_thumbnail"), value=settings.embed_thumbnail
        )
        self._metadata = ft.Switch(
            label=t("embed_metadata"), value=settings.embed_metadata
        )
        self._prefer_vp9 = ft.Switch(
            label=t("prefer_vp9_video"), value=settings.prefer_vp9_video
        )

        # --- Footer ----------------------------------------------------------
        save_button = primary_button(
            t("save_changes"), icon=ft.Icons.SAVE_OUTLINED, on_click=self._on_save
        )
        self._picker = ft.FilePicker()
        export_button = secondary_button(
            t("export_config"), icon=ft.Icons.UPLOAD_OUTLINED, on_click=self._on_export
        )
        import_button = secondary_button(
            t("import_config"), icon=ft.Icons.DOWNLOAD_OUTLINED, on_click=self._on_import
        )
        footer = ft.Container(
            content=ft.Row(
                [
                    export_button,
                    import_button,
                    ft.Container(expand=True),
                    save_button,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=12, horizontal=16),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
        )

        # --- Sections ---------------------------------------------------------
        appearance = _section(
            ft.Icons.PALETTE_OUTLINED, t("section_appearance"), self._theme_selector
        )
        downloads = _section(
            ft.Icons.DOWNLOAD_OUTLINED,
            t("section_downloads"),
            self._folder,
            ft.Column([self._concurrent_label, self._concurrent], spacing=2),
            ft.Column([self._fragments_label, self._fragments], spacing=2),
            self._subtitles,
            self._subtitle_langs,
            self._multi_audio,
        )
        network = _section(
            ft.Icons.PUBLIC_OUTLINED,
            t("section_network"),
            self._proxy,
            ft.Row([self._cookies, self._rate_limit], spacing=12, wrap=True),
            self._headers,
        )
        conversion = _section(
            ft.Icons.TUNE_OUTLINED,
            t("section_conversion"),
            ft.Row(
                [
                    self._keep_originals,
                    self._thumbnail,
                    self._metadata,
                    self._prefer_vp9,
                ],
                spacing=16,
                wrap=True,
            ),
        )

        left = ft.Column(
            [appearance, downloads, network, conversion],
            spacing=16,
            expand=8,
            scroll=ft.ScrollMode.AUTO,
        )
        self._deps_column = ft.Column(
            [
                ft.Text(t("section_dependencies"), style=theme.headline_md()),
                ffmpeg_card,
                js_card,
            ],
            spacing=12,
            expand=4,
        )
        right = self._deps_column

        self.controls = [
            ft.Column(
                [
                    ft.Text(t("settings_title"), style=theme.headline_xl()),
                    ft.Text(
                        t("settings_subtitle"),
                        style=theme.body_sm(ft.Colors.ON_SURFACE_VARIANT),
                    ),
                ],
                spacing=2,
            ),
            ft.Row(
                [left, right],
                spacing=24,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            footer,
        ]

    def did_mount(self) -> None:
        if self._picker not in self.page.services:
            self.page.services.append(self._picker)

    # ------------------------------------------------------------------

    def _build_ffmpeg_card(self) -> ft.Container:
        location = self.ctx.ffmpeg.resolve()
        help_url = None
        if location.source == "path":
            text = f"{t('ffmpeg_system')} · {location.ffmpeg_path}"
            icon, color = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN
        elif location.source == "bundled_full":
            text = t("ffmpeg_bundled_full")
            icon, color = ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN
        elif location.source == "bundled":
            text = t("ffmpeg_bundled")
            icon, color = ft.Icons.WARNING, ft.Colors.ORANGE
            help_url = INSTALL_FFMPEG_URL
        else:
            text = t("ffmpeg_missing")
            icon, color = ft.Icons.ERROR, ft.Colors.RED
            help_url = INSTALL_FFMPEG_URL
        return _status_card(
            t("ffmpeg_status"), text, icon, color, help_url=help_url
        )

    def refresh_dependencies(self) -> None:
        """Rebuild the FFmpeg status card (toolchain download finished)."""
        self._deps_column.controls[1] = self._build_ffmpeg_card()
        safe_update(self)

    # ------------------------------------------------------------------

    async def _on_export(self, e: ft.Event) -> None:
        target = await self._picker.save_file(
            dialog_title=t("export_config"),
            file_name="video_downloader_config.json",
            allowed_extensions=["json"],
        )
        if target:
            self.ctx.settings_repo.export_to(Path(target), self.ctx.settings)
            show_toast(self.ctx.page, t("exported"))

    async def _on_import(self, e: ft.Event) -> None:
        files = await self._picker.pick_files(
            dialog_title=t("import_config"), allowed_extensions=["json"]
        )
        if not files or not files[0].path:
            return
        try:
            self.ctx.settings = self.ctx.settings_repo.import_from(Path(files[0].path))
            self.ctx.save_settings()
        except (ValueError, TypeError, OSError):
            return
        self._apply_to_form(self.ctx.settings)
        self.ctx.apply_theme_mode(self.ctx.settings.theme_mode, False)
        show_toast(self.ctx.page, t("imported"))
        self.page.update()

    def _apply_to_form(self, settings) -> None:
        self._folder.set_value(settings.download_path)
        self._concurrent.value = settings.max_concurrent
        self._concurrent_label.value = f"{t('max_concurrent')}: {settings.max_concurrent}"
        self._fragments.value = settings.concurrent_fragments
        self._fragments_label.value = (
            f"{t('concurrent_fragments')}: {settings.concurrent_fragments}"
        )
        self._proxy.value = settings.proxy
        self._cookies.value = settings.cookies_browser
        self._headers.value = "\n".join(
            f"{k}: {v}" for k, v in settings.custom_headers.items()
        )
        self._rate_limit.value = str(settings.rate_limit_kbps)
        self._keep_originals.value = settings.keep_originals
        self._subtitles.value = settings.write_subtitles
        self._subtitle_langs.value = ", ".join(settings.subtitle_langs)
        self._multi_audio.value = settings.multi_audio
        self._thumbnail.value = settings.embed_thumbnail
        self._metadata.value = settings.embed_metadata
        self._prefer_vp9.value = settings.prefer_vp9_video
        self._theme_selector.set_value(settings.theme_mode)

    def _sync_theme_selector(self) -> None:
        """Keep the selector in sync when the sidebar toggle changes the theme."""
        if self._theme_selector.value != self.ctx.settings.theme_mode:
            self._theme_selector.set_value(self.ctx.settings.theme_mode)

    def _on_concurrent_change(self, e: ft.Event) -> None:
        self._concurrent_label.value = (
            f"{t('max_concurrent')}: {int(self._concurrent.value or 1)}"
        )
        self.update()

    def _on_fragments_change(self, e: ft.Event) -> None:
        self._fragments_label.value = (
            f"{t('concurrent_fragments')}: {int(self._fragments.value or 1)}"
        )
        self.update()

    def _on_theme_change(self, mode: str) -> None:
        # Apply live; persisted only when the user saves (like before).
        self.ctx.apply_theme_mode(mode, False)

    def _on_save(self, e: ft.Event) -> None:
        settings = self.ctx.settings
        settings.download_dir = str(self._folder.value)
        settings.max_concurrent = int(self._concurrent.value or 1)
        settings.concurrent_fragments = int(self._fragments.value or 1)
        settings.proxy = (self._proxy.value or "").strip()
        settings.cookies_browser = self._cookies.value or ""
        settings.custom_headers = _parse_headers(self._headers.value or "")
        try:
            settings.rate_limit_kbps = max(0, int(self._rate_limit.value or "0"))
        except ValueError:
            settings.rate_limit_kbps = 0
        settings.keep_originals = bool(self._keep_originals.value)
        settings.write_subtitles = bool(self._subtitles.value)
        settings.subtitle_langs = [
            lang.strip()
            for lang in (self._subtitle_langs.value or "").split(",")
            if lang.strip()
        ] or ["all"]
        settings.multi_audio = bool(self._multi_audio.value)
        settings.embed_thumbnail = bool(self._thumbnail.value)
        settings.embed_metadata = bool(self._metadata.value)
        settings.prefer_vp9_video = bool(self._prefer_vp9.value)
        settings.theme_mode = self._theme_selector.value or "system"

        self.ctx.save_settings()
        show_toast(self.ctx.page, t("saved"))
