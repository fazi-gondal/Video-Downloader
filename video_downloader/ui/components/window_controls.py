"""In-app window controls (traffic-light dots) for the frameless window.

The native title bar is hidden on desktop; these dots live at the top-right
of the content area: green = maximize/restore, amber = minimize, red = close.
"""

from __future__ import annotations

import flet as ft

from video_downloader.ui import theme
from video_downloader.ui.texts import t
from video_downloader.ui.utils import safe_update

_DOT_SIZE = 13

_GREEN = "#43A047"
_AMBER = "#F59E0B"
_RED = "#EF5350"


class _WindowDot(ft.Container):
    def __init__(self, color: str, tooltip: str, on_click) -> None:
        super().__init__(
            width=_DOT_SIZE,
            height=_DOT_SIZE,
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
            bgcolor=ft.Colors.with_opacity(0.7, color),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, "#000000")),
            tooltip=tooltip,
            on_click=on_click,
        )
        self._color = color
        self.on_hover = self._handle_hover

    def _handle_hover(self, e: ft.Event) -> None:
        entering = e.data is True or e.data == "true"
        self.bgcolor = (
            self._color if entering else ft.Colors.with_opacity(0.7, self._color)
        )
        self.scale = 1.15 if entering else 1.0
        safe_update(self)


class WindowControls(ft.Row):
    """Green (maximize/restore) · amber (minimize) · red (close)."""

    def __init__(self, page: ft.Page) -> None:
        super().__init__()
        self._page = page
        self.spacing = 8
        self.controls = [
            _WindowDot(_GREEN, t("window_maximize"), self._on_maximize),
            _WindowDot(_AMBER, t("window_minimize"), self._on_minimize),
            _WindowDot(_RED, t("window_close"), self._on_close),
        ]

    def _on_maximize(self, e: ft.Event) -> None:
        self._page.window.maximized = not self._page.window.maximized
        self._page.update()

    def _on_minimize(self, e: ft.Event) -> None:
        self._page.window.minimized = True
        self._page.update()

    async def _on_close(self, e: ft.Event) -> None:
        await self._page.window.close()
