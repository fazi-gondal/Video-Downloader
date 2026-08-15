"""Uppercase status pills with tinted background, per the design system."""

from __future__ import annotations

import flet as ft

from video_downloader.models.download import DownloadState
from video_downloader.ui import theme

# Mid-tone semantic colors that hold AA-ish contrast on both dark and light
# tinted backgrounds (the pill text is the saturated color itself).
PILL_CORAL = "#FF5C49"
PILL_TEAL = "#2BB3A8"
PILL_GREEN = "#4CAF50"
PILL_RED = "#EF5350"
PILL_AMBER = "#F59E0B"
PILL_BLUE = "#42A5F5"
PILL_PURPLE = "#AB7DF6"
PILL_GREY = "#9BA1A6"

STATE_PILL_COLORS: dict[DownloadState, str] = {
    DownloadState.PENDING: PILL_GREY,
    DownloadState.PREPARING: PILL_AMBER,
    DownloadState.DOWNLOADING: PILL_CORAL,
    DownloadState.PROCESSING: PILL_TEAL,
    DownloadState.COMPLETED: PILL_GREEN,
    DownloadState.ERROR: PILL_RED,
    DownloadState.CANCELLED: PILL_GREY,
}


class StatusPill(ft.Container):
    """Mutable pill: `set_state(text, color)` restyles it in place."""

    def __init__(self, text: str = "", color: str = PILL_GREY) -> None:
        super().__init__(
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
            padding=ft.Padding.symmetric(vertical=3, horizontal=10),
        )
        self._text = ft.Text("")
        self.content = self._text
        self.set_state(text, color)

    def set_state(self, text: str, color: str) -> None:
        self._text.value = text.upper()
        self._text.style = ft.TextStyle(
            size=10.5,
            weight=ft.FontWeight.W_600,
            color=color,
            font_family=theme.FONT_BODY_SEMIBOLD,
            letter_spacing=0.8,
        )
        self.bgcolor = ft.Colors.with_opacity(0.15, color)
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.3, color))


def status_pill(text: str, color: str) -> StatusPill:
    return StatusPill(text, color)
