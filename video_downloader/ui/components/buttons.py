"""Button helpers. The heavy styling lives in the app-level button themes;
these helpers exist so views build consistent variants (incl. the teal one)."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.ui import theme


def primary_button(
    text: str,
    icon: ft.IconData | None = None,
    on_click: Callable | None = None,
    disabled: bool = False,
) -> ft.FilledButton:
    return ft.FilledButton(text, icon=icon, on_click=on_click, disabled=disabled)


def teal_button(
    text: str,
    icon: ft.IconData | None = None,
    on_click: Callable | None = None,
    disabled: bool = False,
) -> ft.FilledButton:
    """Converter-module action button (secondary/teal accent)."""
    return ft.FilledButton(
        text,
        icon=icon,
        on_click=on_click,
        disabled=disabled,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: ft.Colors.SECONDARY,
                ft.ControlState.DISABLED: ft.Colors.SURFACE_CONTAINER_HIGH,
            },
            color={
                ft.ControlState.DEFAULT: ft.Colors.ON_SECONDARY,
                ft.ControlState.DISABLED: ft.Colors.ON_SURFACE_VARIANT,
            },
            icon_color={
                ft.ControlState.DEFAULT: ft.Colors.ON_SECONDARY,
                ft.ControlState.DISABLED: ft.Colors.ON_SURFACE_VARIANT,
            },
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=theme.RADIUS_CONTROL),
            padding=ft.Padding.symmetric(vertical=14, horizontal=22),
            text_style=ft.TextStyle(
                font_family=theme.FONT_HEADLINE, size=15, weight=ft.FontWeight.W_600
            ),
        ),
    )


def secondary_button(
    text: str,
    icon: ft.IconData | None = None,
    on_click: Callable | None = None,
    disabled: bool = False,
) -> ft.OutlinedButton:
    return ft.OutlinedButton(text, icon=icon, on_click=on_click, disabled=disabled)
