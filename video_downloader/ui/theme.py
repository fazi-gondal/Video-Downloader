"""Nocturnal Studio design system: palettes, themes and typography helpers.

Tonal layering instead of Material shadows: hierarchy comes from stacking
surfaces (base -> elevated -> highest) separated by 1px subtle borders.
Coral is the primary accent (downloads / CTAs), teal identifies the
converter module and ffmpeg post-processing.
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

# Families registered in AppShell via page.fonts (assets/fonts/*.ttf).
FONT_HEADLINE = "Space Grotesk"
FONT_BODY = "Inter"
FONT_BODY_MEDIUM = "Inter Medium"
FONT_BODY_SEMIBOLD = "Inter SemiBold"

RADIUS_CARD = 16
RADIUS_CONTROL = 10
RADIUS_PILL = 999


@dataclass(frozen=True)
class Palette:
    """Raw design tokens for one brightness mode."""

    window_bg: str
    surface_base: str
    surface_elevated: str
    surface_highest: str
    surface_inset: str
    border_subtle: str
    border_strong: str
    text: str
    text_muted: str
    accent: str
    accent_hover: str
    on_accent: str
    teal: str
    teal_bright: str
    on_teal: str
    success: str
    error: str
    warning: str
    info: str


DARK = Palette(
    window_bg="#111318",
    surface_base="#16181D",
    surface_elevated="#1E2127",
    surface_highest="#2A2D35",
    surface_inset="#121418",
    border_subtle=ft.Colors.with_opacity(0.08, "#FFFFFF"),
    border_strong=ft.Colors.with_opacity(0.15, "#FFFFFF"),
    text="#E2E2E9",
    text_muted="#9BA1A6",
    accent="#FF5C49",
    accent_hover="#FF7261",
    on_accent="#FFFFFF",
    teal="#32A097",
    teal_bright="#71D7CD",
    on_teal="#00302C",
    success="#4CAF50",
    error="#EF5350",
    warning="#FF9800",
    info="#2196F3",
)

LIGHT = Palette(
    window_bg="#F8F9FF",
    surface_base="#F8F9FF",
    surface_elevated="#FFFFFF",
    surface_highest="#E7E8EE",
    surface_inset="#EDEDF4",
    border_subtle=ft.Colors.with_opacity(0.08, "#000000"),
    border_strong=ft.Colors.with_opacity(0.16, "#000000"),
    text="#1A1C1E",
    text_muted="#44474E",
    accent="#FF5C49",
    accent_hover="#E84A38",
    on_accent="#FFFFFF",
    teal="#006A62",
    teal_bright="#006A62",
    on_teal="#FFFFFF",
    success="#2E7D32",
    error="#C62828",
    warning="#B26A00",
    info="#1565C0",
)


def current(page: ft.Page) -> Palette:
    """Resolve the active palette from the page's theme mode."""
    mode = page.theme_mode
    if mode == ft.ThemeMode.LIGHT:
        return LIGHT
    if mode == ft.ThemeMode.DARK:
        return DARK
    # SYSTEM: follow the OS brightness.
    if page.platform_brightness == ft.Brightness.LIGHT:
        return LIGHT
    return DARK


# ---------------------------------------------------------------------------
# Typography
#
# Default color is the ON_SURFACE role (not None): with a custom ColorScheme,
# Flutter's fallback text color stays white in BOTH modes, so every style must
# carry a theme-aware color explicitly.


def headline_xl(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    return ft.TextStyle(
        font_family=FONT_HEADLINE, size=28, weight=ft.FontWeight.W_700,
        letter_spacing=-0.5, color=color,
    )


def headline_lg(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    return ft.TextStyle(
        font_family=FONT_HEADLINE, size=24, weight=ft.FontWeight.W_600, color=color
    )


def headline_md(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    return ft.TextStyle(
        font_family=FONT_HEADLINE, size=18, weight=ft.FontWeight.W_600, color=color
    )


def body_lg(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    return ft.TextStyle(font_family=FONT_BODY, size=16, color=color)


def body_md(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    return ft.TextStyle(font_family=FONT_BODY, size=14, color=color)


def body_sm(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    return ft.TextStyle(font_family=FONT_BODY, size=13, color=color)


def label_md(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    return ft.TextStyle(
        font_family=FONT_BODY_MEDIUM, size=12, weight=ft.FontWeight.W_500,
        letter_spacing=0.6, color=color,
    )


def data_style(color: str = ft.Colors.ON_SURFACE) -> ft.TextStyle:
    """Live metrics (speed, ETA, sizes). Always Inter, never Space Grotesk."""
    return ft.TextStyle(
        font_family=FONT_BODY_MEDIUM, size=13, weight=ft.FontWeight.W_500, color=color
    )


# ---------------------------------------------------------------------------
# Flet themes


def _color_scheme(p: Palette) -> ft.ColorScheme:
    return ft.ColorScheme(
        primary=p.accent,
        on_primary=p.on_accent,
        primary_container=ft.Colors.with_opacity(0.15, p.accent),
        on_primary_container=p.accent,
        secondary=p.teal,
        on_secondary=p.on_teal,
        secondary_container=ft.Colors.with_opacity(0.18, p.teal),
        on_secondary_container=p.teal_bright,
        tertiary=p.warning,
        on_tertiary="#FFFFFF",
        error=p.error,
        on_error="#FFFFFF",
        error_container=ft.Colors.with_opacity(0.15, p.error),
        on_error_container=p.error,
        surface=p.surface_base,
        on_surface=p.text,
        on_surface_variant=p.text_muted,
        surface_container_lowest=p.surface_inset,
        surface_container_low=p.surface_elevated,
        surface_container=p.surface_elevated,
        surface_container_high=p.surface_highest,
        surface_container_highest=p.surface_highest,
        surface_dim=p.window_bg,
        surface_bright=p.surface_highest,
        outline=p.border_strong,
        outline_variant=p.border_subtle,
        surface_tint=ft.Colors.TRANSPARENT,
        inverse_surface=p.text,
        on_inverse_surface=p.surface_base,
        inverse_primary=p.accent,
        shadow=ft.Colors.TRANSPARENT,
    )


def _text_theme(p: Palette) -> ft.TextTheme:
    # Literal palette colors (not roles): each mode's Theme carries its own
    # fully-colored TextTheme so DefaultTextStyle is never the white fallback.
    return ft.TextTheme(
        headline_large=headline_xl(p.text),
        headline_medium=headline_lg(p.text),
        headline_small=headline_md(p.text),
        title_large=headline_lg(p.text),
        title_medium=headline_md(p.text),
        title_small=ft.TextStyle(
            font_family=FONT_HEADLINE, size=15, weight=ft.FontWeight.W_600,
            color=p.text,
        ),
        body_large=body_lg(p.text),
        body_medium=body_md(p.text),
        body_small=body_sm(p.text),
        label_large=ft.TextStyle(
            font_family=FONT_BODY_MEDIUM, size=14, weight=ft.FontWeight.W_500,
            color=p.text,
        ),
        label_medium=label_md(p.text),
        label_small=ft.TextStyle(
            font_family=FONT_BODY_MEDIUM, size=11, weight=ft.FontWeight.W_500,
            letter_spacing=0.5, color=p.text,
        ),
    )


def _build_theme(p: Palette) -> ft.Theme:
    control_shape = ft.RoundedRectangleBorder(radius=RADIUS_CONTROL)
    return ft.Theme(
        use_material3=True,
        font_family=FONT_BODY,
        color_scheme=_color_scheme(p),
        text_theme=_text_theme(p),
        scaffold_bgcolor=p.window_bg,
        divider_color=p.border_subtle,
        hover_color=ft.Colors.with_opacity(0.05, p.text),
        splash_color=ft.Colors.with_opacity(0.08, p.text),
        highlight_color=ft.Colors.with_opacity(0.06, p.text),
        card_theme=ft.CardTheme(
            color=p.surface_elevated,
            elevation=0,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
            margin=ft.Margin.all(0),
        ),
        filled_button_theme=ft.FilledButtonTheme(
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: p.accent,
                    ft.ControlState.HOVERED: p.accent_hover,
                    ft.ControlState.DISABLED: p.surface_highest,
                },
                color={
                    ft.ControlState.DEFAULT: p.on_accent,
                    ft.ControlState.DISABLED: p.text_muted,
                },
                icon_color={
                    ft.ControlState.DEFAULT: p.on_accent,
                    ft.ControlState.DISABLED: p.text_muted,
                },
                overlay_color=ft.Colors.TRANSPARENT,
                elevation=0,
                shape=control_shape,
                padding=ft.Padding.symmetric(vertical=14, horizontal=22),
                text_style=ft.TextStyle(
                    font_family=FONT_HEADLINE, size=15, weight=ft.FontWeight.W_600
                ),
            )
        ),
        outlined_button_theme=ft.OutlinedButtonTheme(
            style=ft.ButtonStyle(
                color=p.text,
                icon_color=p.text_muted,
                bgcolor={
                    ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
                    ft.ControlState.HOVERED: p.surface_highest,
                },
                overlay_color=ft.Colors.TRANSPARENT,
                side=ft.BorderSide(1, p.border_strong),
                shape=control_shape,
                padding=ft.Padding.symmetric(vertical=14, horizontal=18),
                text_style=ft.TextStyle(
                    font_family=FONT_BODY_MEDIUM, size=14, weight=ft.FontWeight.W_500
                ),
            )
        ),
        text_button_theme=ft.TextButtonTheme(
            style=ft.ButtonStyle(
                color=p.accent,
                shape=control_shape,
                text_style=ft.TextStyle(
                    font_family=FONT_BODY_MEDIUM, size=14, weight=ft.FontWeight.W_500
                ),
            )
        ),
        icon_button_theme=ft.IconButtonTheme(
            style=ft.ButtonStyle(
                shape=control_shape,
                overlay_color=ft.Colors.with_opacity(0.08, p.text),
            )
        ),
        checkbox_theme=ft.CheckboxTheme(
            fill_color={
                ft.ControlState.SELECTED: p.accent,
                ft.ControlState.DEFAULT: ft.Colors.TRANSPARENT,
            },
            check_color={ft.ControlState.DEFAULT: p.on_accent},
            border_side=ft.BorderSide(1.5, p.text_muted),
            shape=ft.RoundedRectangleBorder(radius=4),
        ),
        switch_theme=ft.SwitchTheme(
            thumb_color={
                ft.ControlState.SELECTED: p.on_accent,
                ft.ControlState.DEFAULT: p.text_muted,
            },
            track_color={
                ft.ControlState.SELECTED: p.accent,
                ft.ControlState.DEFAULT: p.surface_highest,
            },
            track_outline_color={
                ft.ControlState.SELECTED: ft.Colors.TRANSPARENT,
                ft.ControlState.DEFAULT: p.border_strong,
            },
        ),
        slider_theme=ft.SliderTheme(
            active_track_color=p.accent,
            inactive_track_color=p.surface_highest,
            thumb_color=p.accent,
            overlay_color=ft.Colors.with_opacity(0.12, p.accent),
            value_indicator_color=p.surface_highest,
            value_indicator_text_style=data_style(p.text),
        ),
        progress_indicator_theme=ft.ProgressIndicatorTheme(
            color=p.accent,
            linear_track_color=p.surface_highest,
            border_radius=ft.BorderRadius.all(RADIUS_PILL),
        ),
        scrollbar_theme=ft.ScrollbarTheme(
            thumb_color={ft.ControlState.DEFAULT: ft.Colors.with_opacity(0.25, p.text)},
            radius=8,
            thickness={ft.ControlState.DEFAULT: 6},
        ),
        data_table_theme=ft.DataTableTheme(
            heading_row_color={
                ft.ControlState.DEFAULT: ft.Colors.with_opacity(0.5, p.surface_highest)
            },
            data_row_color={
                ft.ControlState.SELECTED: ft.Colors.with_opacity(0.10, p.accent),
                ft.ControlState.HOVERED: ft.Colors.with_opacity(0.35, p.surface_highest),
            },
            heading_text_style=label_md(p.text_muted),
            data_text_style=data_style(p.text),
            divider_thickness=1,
        ),
        dropdown_theme=ft.DropdownTheme(text_style=body_md(p.text)),
        expansion_tile_theme=ft.ExpansionTileTheme(
            bgcolor=p.surface_elevated,
            collapsed_bgcolor=p.surface_elevated,
            icon_color=p.text_muted,
            collapsed_icon_color=p.text_muted,
            text_color=p.text,
            collapsed_text_color=p.text,
            shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
            collapsed_shape=ft.RoundedRectangleBorder(radius=RADIUS_CARD),
        ),
        tooltip_theme=ft.TooltipTheme(text_style=body_sm("#FFFFFF")),
    )


def light_theme() -> ft.Theme:
    return _build_theme(LIGHT)


def dark_theme() -> ft.Theme:
    return _build_theme(DARK)


def theme_mode_from_setting(value: str) -> ft.ThemeMode:
    return {
        "light": ft.ThemeMode.LIGHT,
        "dark": ft.ThemeMode.DARK,
    }.get(value, ft.ThemeMode.SYSTEM)
