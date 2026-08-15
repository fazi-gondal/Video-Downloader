"""Home: hero with URL analysis, entry point to download configuration."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

import flet as ft

from video_downloader.config.constants import ANALYSIS_TIMEOUT_SECONDS
from video_downloader.core.errors import AppError
from video_downloader.models.media import MediaInfo, PlaylistInfo
from video_downloader.services.ytdlp_service import formats_for_display
from video_downloader.ui import theme
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.buttons import primary_button, secondary_button
from video_downloader.ui.components.format_table import FormatTable
from video_downloader.ui.components.media_card import MediaCard
from video_downloader.ui.components.playlist_selector import PlaylistSelector
from video_downloader.ui.components.skeleton import MediaCardSkeleton
from video_downloader.ui.texts import t
from video_downloader.ui.utils import run_task, safe_update

logger = logging.getLogger(__name__)

_SERVICES: list[tuple[str, ft.IconData]] = [
    ("YouTube", ft.Icons.SMART_DISPLAY_OUTLINED),
    ("TikTok", ft.Icons.MUSIC_NOTE_OUTLINED),
    ("Instagram", ft.Icons.PHOTO_CAMERA_OUTLINED),
]

_SEARCH_BAR_MAX_WIDTH = 680


class DashboardView(ft.Column):
    def __init__(self, ctx: AppContext, on_continue: Callable[[], None]) -> None:
        super().__init__()
        self.ctx = ctx
        self.on_continue = on_continue
        self.expand = True
        self.spacing = 16
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        # --- Search bar (shared between hero and results states) ----------
        self._url_field = ft.TextField(
            hint_text=t("url_hint"),
            expand=True,
            border=ft.InputBorder.NONE,
            text_style=theme.body_lg(),
            on_submit=self._on_analyze,
        )
        self._analyze_button = primary_button(
            t("analyze"), icon=ft.Icons.ARROW_FORWARD, on_click=self._on_analyze
        )
        self._search_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.LINK, size=20, color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                        padding=ft.Padding(left=14, top=0, right=2, bottom=0),
                    ),
                    self._url_field,
                    self._analyze_button,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=6,
            width=_SEARCH_BAR_MAX_WIDTH,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD - 2),
        )

        # --- Hero-only blocks ---------------------------------------------
        self._claim = ft.Column(
            [
                ft.Text(
                    spans=[
                        ft.TextSpan(t("hero_title_lead"), style=theme.headline_xl()),
                        ft.TextSpan(
                            t("hero_title_accent"),
                            style=theme.headline_xl(ft.Colors.PRIMARY),
                        ),
                    ],
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    content=ft.Text(
                        t("hero_subtitle"),
                        style=theme.body_lg(ft.Colors.ON_SURFACE_VARIANT),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    width=520,
                ),
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._services = ft.Column(
            [
                ft.Text(
                    t("supported_services").upper(),
                    style=theme.label_md(ft.Colors.ON_SURFACE_VARIANT),
                ),
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(
                                    icon,
                                    size=18,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Text(
                                    name,
                                    size=14,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                            spacing=6,
                            tight=True,
                        )
                        for name, icon in _SERVICES
                    ],
                    spacing=28,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=14,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            opacity=0.7,
        )

        # --- Analysis feedback ---------------------------------------------
        self._skeleton = MediaCardSkeleton()
        self._busy = ft.Row(
            [
                ft.ProgressRing(width=16, height=16, stroke_width=2),
                ft.Text(t("analyzing"), color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            spacing=10,
            visible=False,
            alignment=ft.MainAxisAlignment.CENTER,
        )
        self._error_text = ft.Text(color=ft.Colors.ERROR, expand=True)
        self._error_banner = ft.Container(
            visible=False,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.4, ft.Colors.ERROR)),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL + 2),
            padding=14,
            width=_SEARCH_BAR_MAX_WIDTH,
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ERROR_OUTLINE, color=ft.Colors.ERROR, size=20),
                    self._error_text,
                ],
                spacing=10,
            ),
        )

        # --- Results --------------------------------------------------------
        self._results = ft.Column(spacing=16, width=880)
        self._results_scroll = ft.Column(
            [
                self._skeleton,
                self._results,
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            visible=False,
            spacing=16,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self._skeleton.visible = False

        self._top_spacer = ft.Container(expand=3)
        self._bottom_spacer = ft.Container(expand=4)

        self.controls = [
            self._top_spacer,
            self._claim,
            ft.Container(height=8, visible=True),
            self._search_bar,
            self._busy,
            self._error_banner,
            self._services,
            self._results_scroll,
            self._bottom_spacer,
        ]

    # ------------------------------------------------------------------

    def _set_hero_mode(self, hero: bool) -> None:
        """Hero = claim centered vertically; otherwise search bar on top."""
        self._top_spacer.visible = hero
        self._bottom_spacer.visible = hero
        self._claim.visible = hero
        self._services.visible = hero
        self._results_scroll.visible = not hero

    async def _on_analyze(self, e: ft.Event) -> None:
        url = (self._url_field.value or "").strip()
        if not url:
            self._show_error(t("error_unsupported_url"))
            return

        self._set_busy(True)
        self._results.controls.clear()
        self.ctx.current_media = None
        self.ctx.selected_entries = []
        self._set_hero_mode(False)
        self._skeleton.visible = True
        self.update()
        run_task(self, self._skeleton.pulse)
        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(self.ctx.ytdlp.analyze, url),
                timeout=ANALYSIS_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            logger.warning("Analysis timed out after %ss for %s", ANALYSIS_TIMEOUT_SECONDS, url)
            self._show_error(t("error_analysis_timeout"))
        except AppError as err:
            logger.warning("Analysis failed (%s): %s", err.user_message_key, err.detail or err)
            self._show_error(t(err.user_message_key))
        except Exception:
            logger.exception("Unexpected analysis error for %s", url)
            self._show_error(t("error_generic"))
        else:
            self.ctx.current_media = result
            if isinstance(result, PlaylistInfo):
                self.ctx.selected_entries = list(result.entries)
            self._render_result(result)
        finally:
            self._skeleton.visible = False
            self._set_busy(False)

    def _render_result(self, media: MediaInfo | PlaylistInfo) -> None:
        self._results.controls.clear()
        self._results.controls.append(MediaCard(media))

        if isinstance(media, PlaylistInfo):
            selector = PlaylistSelector(media.entries, on_change=self._on_selection_change)
            self._results.controls.append(
                ft.Text(t("playlist_detected"), style=theme.headline_md())
            )
            self._results.controls.append(selector)
        else:
            self._formats_section = ft.Column(spacing=8)
            self._formats_button = secondary_button(
                t("explore_formats"),
                icon=ft.Icons.TABLE_ROWS_OUTLINED,
                on_click=self._on_explore_formats,
            )
            self._results.controls.append(
                ft.Row([self._formats_button], alignment=ft.MainAxisAlignment.START)
            )
            self._results.controls.append(self._formats_section)

        self._results.controls.append(
            ft.Row(
                [
                    primary_button(
                        t("continue"),
                        icon=ft.Icons.ARROW_FORWARD,
                        on_click=lambda e: self.on_continue(),
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )
        self._set_hero_mode(False)
        self.update()

    async def _on_explore_formats(self, e: ft.Event) -> None:
        media = self.ctx.current_media
        if not isinstance(media, MediaInfo):
            return

        # Toggle: a visible table collapses on the second click
        if self._formats_section.controls:
            self._formats_section.controls.clear()
            self._formats_button.content = t("explore_formats")
            self.update()
            return

        if media.formats:
            self._show_format_table(media)
            return

        self._formats_button.disabled = True
        self._formats_button.content = t("loading_formats")
        self.update()
        try:
            full = await asyncio.wait_for(
                asyncio.to_thread(self.ctx.ytdlp.fetch_formats, media.webpage_url),
                timeout=ANALYSIS_TIMEOUT_SECONDS,
            )
        except TimeoutError:
            self._show_error(t("error_analysis_timeout"))
            self._formats_button.content = t("explore_formats")
        except AppError as err:
            self._show_error(t(err.user_message_key))
            self._formats_button.content = t("explore_formats")
        else:
            media.formats = full.formats
            self.ctx.current_media = media
            self._show_format_table(media)
        finally:
            self._formats_button.disabled = False
            self.update()

    def _show_format_table(self, media: MediaInfo) -> None:
        self._formats_section.controls = [
            FormatTable(formats_for_display(media))
        ]
        self._formats_button.content = t("hide_formats")
        self.update()

    # ------------------------------------------------------------------

    def _on_selection_change(self, selected) -> None:
        self.ctx.selected_entries = selected

    def _set_busy(self, busy: bool) -> None:
        self._busy.visible = busy
        self._analyze_button.disabled = busy
        self._url_field.disabled = busy
        if busy:
            self._error_banner.visible = False
        safe_update(self)

    def _show_error(self, message: str) -> None:
        self._error_text.value = message
        self._error_banner.visible = True
        # No results to show: bring the hero layout back around the banner.
        if not self._results.controls:
            self._set_hero_mode(True)
            self._results_scroll.visible = False
        safe_update(self)
