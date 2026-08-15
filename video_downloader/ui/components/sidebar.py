"""Custom navigation sidebar (replaces NavigationRail).

220px wide with brand header, five destinations (active = coral edge bar +
tonal background), a live downloads badge, and a footer with the ffmpeg
status chip and the theme toggle. Collapses to icons-only on narrow windows.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.ui import theme
from video_downloader.ui.components.status_pill import (
    PILL_AMBER,
    PILL_GREEN,
    PILL_RED,
)
from video_downloader.ui.texts import t
from video_downloader.ui.utils import safe_update

EXPANDED_WIDTH = 220
COLLAPSED_WIDTH = 76

_DESTINATIONS: list[tuple[str, ft.IconData, ft.IconData]] = [
    ("nav_dashboard", ft.Icons.HOME_FILLED, ft.Icons.HOME_FILLED),
    ("nav_downloads", ft.Icons.DOWNLOAD_ROUNDED, ft.Icons.DOWNLOAD),
    ("nav_converter", ft.Icons.SWAP_HORIZ_OUTLINED, ft.Icons.SWAP_HORIZ),
    ("nav_history", ft.Icons.HISTORY, ft.Icons.HISTORY),
    ("nav_settings", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS),
    ("nav_about", ft.Icons.INFO_OUTLINED, ft.Icons.INFO),
]

_FFMPEG_CHIP: dict[str, tuple[str, str]] = {
    "path": (PILL_GREEN, "ffmpeg_chip_ok"),
    "bundled_full": (PILL_GREEN, "ffmpeg_chip_ok"),
    "bundled": (PILL_AMBER, "ffmpeg_chip_partial"),
    "missing": (PILL_RED, "ffmpeg_chip_missing"),
}


class _SidebarItem(ft.Container):
    def __init__(self, label: str, icon: ft.IconData, selected_icon: ft.IconData,
                 on_click: Callable) -> None:
        super().__init__(
            padding=ft.Padding(left=8, top=9, right=12, bottom=9),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
            on_click=on_click,
        )
        self.on_hover = self._handle_hover
        self._icon_data = icon
        self._selected_icon_data = selected_icon
        self._label_value = label
        self._active = False

        self._edge = ft.Container(
            width=3.5,
            height=22,
            bgcolor=ft.Colors.TRANSPARENT,
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
        )
        self._icon_ctl = ft.Icon(icon, size=21, color=ft.Colors.ON_SURFACE_VARIANT)
        self._label_ctl = ft.Text(
            label, size=14, color=ft.Colors.ON_SURFACE_VARIANT, no_wrap=True
        )
        self._badge_text = ft.Text(
            "0", size=10, weight=ft.FontWeight.W_700, color=ft.Colors.ON_PRIMARY
        )
        self._badge_ctl = ft.Container(
            content=self._badge_text,
            bgcolor=ft.Colors.PRIMARY,
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
            padding=ft.Padding.symmetric(vertical=2, horizontal=7),
            visible=False,
        )
        self._spacer = ft.Container(expand=True)
        self._row = ft.Row(
            [self._edge, self._icon_ctl, self._label_ctl, self._spacer, self._badge_ctl],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.content = self._row

    def set_active(self, active: bool) -> None:
        self._active = active
        self._edge.bgcolor = ft.Colors.PRIMARY if active else ft.Colors.TRANSPARENT
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH if active else None
        self._icon_ctl.icon = self._selected_icon_data if active else self._icon_data
        self._icon_ctl.color = (
            ft.Colors.PRIMARY if active else ft.Colors.ON_SURFACE_VARIANT
        )
        self._label_ctl.color = (
            ft.Colors.ON_SURFACE if active else ft.Colors.ON_SURFACE_VARIANT
        )
        self._label_ctl.weight = (
            ft.FontWeight.W_600 if active else ft.FontWeight.W_400
        )

    def set_badge(self, count: int) -> None:
        self._badge_text.value = str(count)
        self._badge_ctl.visible = count > 0

    def set_collapsed(self, collapsed: bool) -> None:
        self._label_ctl.visible = not collapsed
        self._spacer.visible = not collapsed
        self.tooltip = self._label_value if collapsed else None
        self._row.alignment = (
            ft.MainAxisAlignment.CENTER if collapsed else ft.MainAxisAlignment.START
        )

    def _handle_hover(self, e: ft.Event) -> None:
        if self._active:
            return
        entering = e.data is True or e.data == "true"
        self.bgcolor = (
            ft.Colors.with_opacity(0.6, ft.Colors.SURFACE_CONTAINER_HIGH)
            if entering
            else None
        )
        safe_update(self)


class Sidebar(ft.Container):
    def __init__(
        self,
        on_select: Callable[[int], None],
        on_toggle_theme: Callable[[], None],
        ffmpeg_source: str,
        draggable: bool = False,
    ) -> None:
        super().__init__(
            width=EXPANDED_WIDTH,
            padding=ft.Padding(left=12, top=18, right=12, bottom=14),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border(right=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            animate=ft.Animation(180, ft.AnimationCurve.EASE_OUT),
        )
        self._on_select = on_select
        self._collapsed = False

        # Brand -----------------------------------------------------------
        logo = ft.Container(
            content=ft.Icon(ft.Icons.DOWNLOAD, size=22, color=ft.Colors.ON_PRIMARY),
            width=40,
            height=40,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.PRIMARY,
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
        )
        self._brand_texts = ft.Column(
            [
                ft.Text(
                    t("app_title"),
                    size=15,
                    weight=ft.FontWeight.W_700,
                    font_family=theme.FONT_HEADLINE,
                    color=ft.Colors.ON_SURFACE,
                    no_wrap=True,
                ),
                ft.Text(
                    t("brand_subtitle"),
                    size=11,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    no_wrap=True,
                ),
            ],
            spacing=1,
        )
        brand: ft.Control = ft.Row([logo, self._brand_texts], spacing=10)
        if draggable:
            # Frameless window: the brand header doubles as a drag handle.
            brand = ft.WindowDragArea(brand)

        # Destinations ------------------------------------------------------
        self._items: list[_SidebarItem] = [
            _SidebarItem(t(key), icon, selected, self._make_handler(i))
            for i, (key, icon, selected) in enumerate(_DESTINATIONS)
        ]

        # Footer ------------------------------------------------------------
        self._ffmpeg_text = ft.Text(
            "",
            size=11.5,
            font_family=theme.FONT_BODY_MEDIUM,
            no_wrap=True,
        )
        self._ffmpeg_dot = ft.Container(
            width=8,
            height=8,
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
        )
        self._ffmpeg_chip = ft.Container(
            content=ft.Row(
                [
                    self._ffmpeg_dot,
                    self._ffmpeg_text,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
            padding=ft.Padding.symmetric(vertical=8, horizontal=12),
        )
        self.set_ffmpeg_status(ffmpeg_source)
        self._theme_icon = ft.Icon(
            ft.Icons.DARK_MODE_OUTLINED, size=19, color=ft.Colors.ON_SURFACE_VARIANT
        )
        self._theme_label = ft.Text(
            t("theme_toggle"),
            size=13.5,
            color=ft.Colors.ON_SURFACE_VARIANT,
            no_wrap=True,
        )
        self._theme_toggle = ft.Container(
            content=ft.Row([self._theme_icon, self._theme_label], spacing=10),
            padding=ft.Padding.symmetric(vertical=9, horizontal=12),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
            on_click=lambda e: on_toggle_theme(),
            on_hover=self._handle_toggle_hover,
        )

        self.content = ft.Column(
            [
                ft.Container(
                    content=brand,
                    padding=ft.Padding(left=4, top=0, right=0, bottom=14),
                ),
                *self._items,
                ft.Container(expand=True),
                self._ffmpeg_chip,
                self._theme_toggle,
            ],
            spacing=4,
        )
        self.set_active(0)

    # ------------------------------------------------------------------

    def _make_handler(self, index: int):
        def handler(e: ft.Event) -> None:
            self._on_select(index)

        return handler

    def set_active(self, index: int) -> None:
        for i, item in enumerate(self._items):
            item.set_active(i == index)

    def set_downloads_badge(self, count: int) -> None:
        self._items[1].set_badge(count)
        safe_update(self)

    def set_ffmpeg_status(self, source: str) -> None:
        """Refresh the footer chip (e.g. after the toolchain download ends)."""
        color, chip_key = _FFMPEG_CHIP.get(source, _FFMPEG_CHIP["missing"])
        self._ffmpeg_dot.bgcolor = color
        self._ffmpeg_text.value = t(chip_key)
        self._ffmpeg_text.color = color
        self._ffmpeg_chip.tooltip = t(chip_key) if self._collapsed else None
        safe_update(self)

    def set_theme_icon(self, is_dark: bool) -> None:
        self._theme_icon.icon = (
            ft.Icons.DARK_MODE_OUTLINED if is_dark else ft.Icons.LIGHT_MODE_OUTLINED
        )
        safe_update(self)

    def set_collapsed(self, collapsed: bool) -> None:
        if collapsed == self._collapsed:
            return
        self._collapsed = collapsed
        self.width = COLLAPSED_WIDTH if collapsed else EXPANDED_WIDTH
        self._brand_texts.visible = not collapsed
        for item in self._items:
            item.set_collapsed(collapsed)
        self._ffmpeg_text.visible = not collapsed
        self._ffmpeg_chip.tooltip = self._ffmpeg_text.value if collapsed else None
        self._theme_label.visible = not collapsed
        self._theme_toggle.tooltip = t("theme_toggle") if collapsed else None
        safe_update(self)

    def _handle_toggle_hover(self, e: ft.Event) -> None:
        entering = e.data is True or e.data == "true"
        self._theme_toggle.bgcolor = (
            ft.Colors.with_opacity(0.6, ft.Colors.SURFACE_CONTAINER_HIGH)
            if entering
            else None
        )
        safe_update(self._theme_toggle)
