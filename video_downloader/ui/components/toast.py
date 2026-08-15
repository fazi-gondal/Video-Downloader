"""Floating toast notifications rendered on the page overlay.

Custom implementation: in Flet 0.85 `page.show_dialog(SnackBar)` renders
nothing, so the toast is a positioned overlay card that fades in, waits,
fades out and removes itself.
"""

from __future__ import annotations

import asyncio

import flet as ft

from video_downloader.ui import theme
from video_downloader.ui.components.status_pill import PILL_GREEN

_VISIBLE_SECONDS = 2.6
_FADE = ft.Animation(250, ft.AnimationCurve.EASE_OUT)


def show_toast(
    page: ft.Page,
    message: str,
    icon: ft.IconData = ft.Icons.CHECK_CIRCLE,
    color: str = PILL_GREEN,
) -> None:
    """Show a short floating confirmation near the bottom of the window."""
    card = ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=18, color=color),
                ft.Text(
                    message,
                    size=13.5,
                    weight=ft.FontWeight.W_500,
                    color=ft.Colors.ON_SURFACE,
                ),
            ],
            spacing=10,
            tight=True,
        ),
        padding=ft.Padding.symmetric(vertical=12, horizontal=20),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL + 2),
        opacity=0,
        animate_opacity=_FADE,
    )
    wrapper = ft.Row([card], alignment=ft.MainAxisAlignment.CENTER)
    wrapper.left = 0
    wrapper.right = 0
    wrapper.bottom = 32

    async def run() -> None:
        page.overlay.append(wrapper)
        page.update()
        await asyncio.sleep(0.05)  # let the 0-opacity frame land first
        card.opacity = 1
        page.update()
        await asyncio.sleep(_VISIBLE_SECONDS)
        card.opacity = 0
        page.update()
        await asyncio.sleep(0.3)
        if wrapper in page.overlay:
            page.overlay.remove(wrapper)
            page.update()

    page.run_task(run)
