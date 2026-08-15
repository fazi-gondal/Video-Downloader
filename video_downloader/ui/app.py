"""Application shell: page setup, theming, navigation and event pump."""

from __future__ import annotations

import asyncio
import importlib
import logging
import threading
from collections.abc import Callable

import flet as ft

from video_downloader.config.constants import APP_TITLE
from video_downloader.config.settings import AppSettings, SettingsRepository
from video_downloader.core.event_bus import EventBus
from video_downloader.core.events import (
    FFmpegToolchainReady,
    TaskQueued,
    TaskStateChanged,
)
from video_downloader.models.download import DownloadState
from video_downloader.models.media import MediaInfo, PlaylistEntry, PlaylistInfo
from video_downloader.services.conversion_service import ConversionService
from video_downloader.services.download_manager import DownloadManager
from video_downloader.services.ffmpeg_service import FFmpegService
from video_downloader.services.history_service import HistoryService
from video_downloader.services.notification_service import NotificationService
from video_downloader.services.ytdlp_service import YtdlpService
from video_downloader.ui import theme
from video_downloader.ui.components.sidebar import Sidebar
from video_downloader.ui.components.window_controls import WindowControls
from video_downloader.ui.texts import t

logger = logging.getLogger(__name__)

# Sidebar collapses below this window width and re-expands above the second
# threshold (hysteresis so resizing near the edge doesn't flicker).
_COLLAPSE_BELOW = 1000
_EXPAND_ABOVE = 1040


class AppContext:
    """Shared services and state, passed to every view."""

    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.settings_repo = SettingsRepository()
        self.settings: AppSettings = self.settings_repo.load()
        self.bus = EventBus()
        self.ffmpeg = FFmpegService()
        self.ytdlp = YtdlpService(self.ffmpeg, lambda: self.settings)
        self.download_manager = DownloadManager(
            self.ytdlp, self.bus, max_concurrent=self.settings.max_concurrent
        )
        self.conversions = ConversionService(self.ffmpeg, self.bus)
        self.history = HistoryService()
        self.notifications = NotificationService()
        # Analysis state shared between dashboard and config views
        self.current_media: MediaInfo | PlaylistInfo | None = None
        self.selected_entries: list[PlaylistEntry] = []
        # Views with theme-dependent literal colors register here; the shell
        # invokes every callback right after page.theme_mode changes.
        self._theme_listeners: list[Callable[[], None]] = []
        # Set by the shell; views (Settings) use it to apply the theme live.
        self.apply_theme_mode: Callable[[str, bool], None] = lambda mode, persist: None

    def save_settings(self) -> None:
        self.settings_repo.save(self.settings)
        self.download_manager.set_max_concurrent(self.settings.max_concurrent)

    def on_theme_change(self, callback: Callable[[], None]) -> None:
        self._theme_listeners.append(callback)

    def notify_theme_changed(self) -> None:
        for callback in self._theme_listeners:
            try:
                callback()
            except Exception:
                logger.exception("Theme-change listener failed")

    @property
    def palette(self) -> theme.Palette:
        return theme.current(self.page)


class AppShell:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.ctx = AppContext(page)
        self.ctx.apply_theme_mode = self.apply_theme_mode
        self._views: list[ft.Control] = []
        self._content = ft.Container(
            expand=True, padding=ft.Padding(left=32, top=24, right=32, bottom=20)
        )
        self._sidebar = Sidebar(
            on_select=self.select_view,
            on_toggle_theme=self._toggle_theme,
            ffmpeg_source=self.ctx.ffmpeg.resolve().source,
            draggable=not page.web,
        )

    # ------------------------------------------------------------------

    def build(self) -> None:
        page = self.page
        page.title = APP_TITLE
        page.fonts = {
            theme.FONT_HEADLINE: "/fonts/SpaceGrotesk-SemiBold.ttf",
            theme.FONT_BODY: "/fonts/Inter-Regular.ttf",
            theme.FONT_BODY_MEDIUM: "/fonts/Inter-Medium.ttf",
            theme.FONT_BODY_SEMIBOLD: "/fonts/Inter-SemiBold.ttf",
        }
        page.theme = theme.light_theme()
        page.dark_theme = theme.dark_theme()
        page.theme_mode = theme.theme_mode_from_setting(self.ctx.settings.theme_mode)
        page.window.width = 1100
        page.window.height = 760
        page.window.min_width = 900
        page.window.min_height = 600
        page.padding = 0
        page.on_resize = self._on_resize

        self._views = self._build_views()
        self._content.content = self._views[0]

        # Frameless look on desktop: hide the native title bar and replace
        # its buttons with in-app controls; the top strip drags the window.
        is_desktop = not page.web
        main_column: list[ft.Control] = []
        if is_desktop:
            page.window.title_bar_hidden = True
            page.window.title_bar_buttons_hidden = True
            main_column.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.WindowDragArea(
                                ft.Container(height=34), expand=True
                            ),
                            WindowControls(page),
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(left=0, top=10, right=18, bottom=0),
                )
            )
            self._content.padding = ft.Padding(left=32, top=2, right=32, bottom=20)
        main_column.append(self._content)

        page.add(
            ft.Row(
                [
                    self._sidebar,
                    ft.Column(main_column, spacing=0, expand=True),
                ],
                expand=True,
                spacing=0,
            )
        )
        self._sidebar.set_theme_icon(theme.current(page) is theme.DARK)
        self._maybe_collapse(page.width)

        # Bridge worker threads -> UI loop, then start consuming events
        self.ctx.bus.attach_loop(asyncio.get_event_loop())
        self.ctx.bus.subscribe(TaskStateChanged, self._on_task_state_changed)
        self.ctx.bus.subscribe(TaskQueued, self._on_task_queued)
        self.ctx.bus.subscribe(FFmpegToolchainReady, self._on_ffmpeg_ready)
        page.run_task(self.ctx.bus.pump)

        # Fetch the full ffmpeg+ffprobe toolchain in the background if needed.
        # The callback runs on the fetch thread; the bus crosses to the UI loop.
        self.ctx.ffmpeg.ensure_full_toolchain(
            on_ready=lambda: self.ctx.bus.publish(FFmpegToolchainReady())
        )

    # ------------------------------------------------------------------
    # Event handlers

    def _on_task_state_changed(self, event: TaskStateChanged) -> None:
        """Record history and notify when a download reaches a terminal state."""
        self._refresh_downloads_badge()
        task = self.ctx.download_manager.get(event.task_id)
        if task is None or not task.is_terminal:
            return
        self.ctx.history.record(task)
        if task.state is DownloadState.COMPLETED:
            self.ctx.notifications.notify(t("notify_done_title"), task.request.title)

    def _on_task_queued(self, event: TaskQueued) -> None:
        self._refresh_downloads_badge()

    def _on_ffmpeg_ready(self, event: FFmpegToolchainReady) -> None:
        """Full toolchain downloaded: refresh status UI and confirm via toast."""
        from video_downloader.ui.components.toast import show_toast

        source = self.ctx.ffmpeg.resolve().source
        self._sidebar.set_ffmpeg_status(source)
        settings_view = self._views[4]
        if hasattr(settings_view, "refresh_dependencies"):
            settings_view.refresh_dependencies()
        show_toast(self.page, t("ffmpeg_ready"))

    def _refresh_downloads_badge(self) -> None:
        active = sum(1 for task in self.ctx.download_manager.tasks() if task.is_active)
        self._sidebar.set_downloads_badge(active)

    def _on_resize(self, e: ft.Event) -> None:
        width = getattr(e, "width", None) or self.page.width
        self._maybe_collapse(width)

    def _maybe_collapse(self, width: float | None) -> None:
        if width is None:
            return
        if width < _COLLAPSE_BELOW:
            self._sidebar.set_collapsed(True)
        elif width >= _EXPAND_ABOVE:
            self._sidebar.set_collapsed(False)

    # ------------------------------------------------------------------
    # Theme

    def _toggle_theme(self) -> None:
        is_dark = theme.current(self.page) is theme.DARK
        self.apply_theme_mode("light" if is_dark else "dark", persist=True)

    def apply_theme_mode(self, mode: str, persist: bool = True) -> None:
        """Switch light/dark/system live; optionally persist to settings."""
        self.page.theme_mode = theme.theme_mode_from_setting(mode)
        self.ctx.settings.theme_mode = mode
        if persist:
            self.ctx.save_settings()
        self._sidebar.set_theme_icon(theme.current(self.page) is theme.DARK)
        self.ctx.notify_theme_changed()
        self.page.update()

    # ------------------------------------------------------------------

    def _build_views(self) -> list[ft.Control]:
        from video_downloader.ui.views.about_view import AboutView
        from video_downloader.ui.views.converter_view import ConverterView
        from video_downloader.ui.views.dashboard_view import DashboardView
        from video_downloader.ui.views.downloads_view import DownloadsView
        from video_downloader.ui.views.history_view import HistoryView
        from video_downloader.ui.views.settings_view import SettingsView

        return [
            DashboardView(self.ctx, on_continue=self.open_config),
            DownloadsView(self.ctx),
            ConverterView(self.ctx),
            HistoryView(self.ctx, on_redownload=lambda: self.select_view(1)),
            SettingsView(self.ctx),
            AboutView(),
        ]

    def select_view(self, index: int) -> None:
        self._sidebar.set_active(index)
        self._content.content = self._views[index]
        self.page.update()

    def open_config(self) -> None:
        """Show the download configuration screen for the analyzed media."""
        from video_downloader.ui.views.config_view import ConfigView

        self._content.content = ConfigView(
            self.ctx,
            on_started=lambda: self.select_view(1),
            on_back=lambda: self.select_view(0),
        )
        self.page.update()


async def main(page: ft.Page) -> None:
    shell = AppShell(page)
    try:
        shell.build()
    finally:
        if not page.web:
            page.window.visible = True
            page.window.focused = True
            page.update()
        # Warm up yt_dlp (imported lazily off the startup path) so the first
        # "Analyze" doesn't pay the import cost on its worker thread.
        threading.Thread(
            target=lambda: importlib.import_module("yt_dlp"), daemon=True
        ).start()
