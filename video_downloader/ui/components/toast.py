"""Floating toast and SnackBar notifications.

In Flet 1.0, ft.SnackBar is a DialogControl rendered via page.show_dialog().
"""

from __future__ import annotations

import asyncio
import logging

import flet as ft

from video_downloader.ui import theme
from video_downloader.ui.components.status_pill import PILL_GREEN

logger = logging.getLogger(__name__)

_VISIBLE_SECONDS = 3.0
_FADE = ft.Animation(250, ft.AnimationCurve.EASE_OUT)


def show_toast(
    page: ft.Page,
    message: str,
    icon: ft.IconData = ft.Icons.CHECK_CIRCLE,
    color: str = PILL_GREEN,
    duration_ms: int = 3500,
) -> None:
    """Show a floating SnackBar confirmation near the bottom of the window."""
    try:
        snack = ft.SnackBar(
            content=ft.Row(
                [
                    ft.Icon(icon, size=18, color=color),
                    ft.Text(
                        message,
                        size=13.5,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.ON_SURFACE,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        expand=True,
                    ),
                ],
                spacing=10,
                tight=False,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            behavior=ft.SnackBarBehavior.FLOATING,
            duration=duration_ms,
            show_close_icon=True,
            close_icon_color=ft.Colors.ON_SURFACE_VARIANT,
        )
        page.show_dialog(snack)
        return
    except Exception:
        logger.debug("page.show_dialog(SnackBar) failed, falling back to overlay", exc_info=True)

    # Fallback to overlay card if show_dialog is unavailable
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
        await asyncio.sleep(0.05)
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


# Alias for callers expecting show_snack_bar
show_snack_bar = show_toast
