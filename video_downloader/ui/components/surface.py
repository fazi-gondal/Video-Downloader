"""Tonal surface containers: the replacement for Material cards.

Elevation comes from surface color + a 1px subtle border, never shadows.
Colors use theme-aware scheme roles so light/dark switching is automatic.
"""

from __future__ import annotations

import flet as ft

from video_downloader.ui import theme


def surface_card(
    content: ft.Control,
    padding: ft.PaddingValue = 20,
    expand: bool | int | None = None,
) -> ft.Container:
    """Level-1 surface: cards, panels, list rows."""
    return ft.Container(
        content=content,
        padding=padding,
        expand=expand,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
    )


def inset_container(
    content: ft.Control,
    padding: ft.PaddingValue | None = None,
    expand: bool | int | None = None,
) -> ft.Container:
    """Sunken surface for inputs/search bars (darker than the base)."""
    if padding is None:
        padding = ft.Padding.symmetric(vertical=6, horizontal=14)
    return ft.Container(
        content=content,
        padding=padding,
        expand=expand,
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL + 2),
    )
