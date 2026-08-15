"""Skeleton placeholders shown while the URL analysis is in flight."""

from __future__ import annotations

import asyncio

import flet as ft

from video_downloader.ui import theme


def _block(width: int | None = None, height: int = 14, expand: bool = False) -> ft.Container:
    return ft.Container(
        width=width,
        height=height,
        expand=expand,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=ft.BorderRadius.all(8),
    )


class MediaCardSkeleton(ft.Container):
    """Shape-matched placeholder for MediaCard, pulsing via animate_opacity."""

    def __init__(self) -> None:
        super().__init__(
            content=ft.Row(
                [
                    _block(width=200, height=112),
                    ft.Column(
                        [
                            _block(width=380, height=20),
                            _block(width=240, height=14),
                            _block(width=160, height=14),
                        ],
                        spacing=10,
                    ),
                ],
                spacing=16,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=20,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
            opacity=1.0,
            animate_opacity=ft.Animation(550, ft.AnimationCurve.EASE_IN_OUT),
        )

    async def pulse(self) -> None:
        """Alternate opacity while mounted and visible; exits quietly."""
        low = False
        try:
            while self.page is not None and self.visible:
                self.opacity = 0.45 if not low else 1.0
                low = not low
                self.update()
                await asyncio.sleep(0.55)
        except Exception:  # noqa: BLE001 - view may unmount mid-animation
            return
