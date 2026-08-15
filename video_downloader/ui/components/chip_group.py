"""Segmented chip selector — replaces dropdowns for small option sets.

API mirrors Dropdown's (`.value` holds the selected label) so callers like
ConfigView._build_requests keep working unchanged.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.ui import theme
from video_downloader.ui.utils import safe_update


class _Chip(ft.Container):
    def __init__(self, label: str, sublabel: str | None, on_click) -> None:
        label_text = ft.Text(
            label,
            size=13,
            weight=ft.FontWeight.W_500,
            no_wrap=True,
            color=ft.Colors.ON_SURFACE,
        )
        texts: list[ft.Control] = [label_text]
        if sublabel:
            texts.append(
                ft.Text(sublabel, size=10.5, color=ft.Colors.ON_SURFACE_VARIANT)
            )
        super().__init__(
            content=ft.Column(
                texts,
                spacing=1,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=8, horizontal=12),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL - 2),
            border=ft.Border.all(1, ft.Colors.TRANSPARENT),
            alignment=ft.Alignment.CENTER,
            on_click=on_click,
            on_hover=self._on_hover,
        )
        self.label_text = label_text
        self.selected = False

    def _on_hover(self, e: ft.Event) -> None:
        if self.selected:
            return
        entering = e.data is True or e.data == "true"
        self.bgcolor = (
            ft.Colors.with_opacity(0.5, ft.Colors.SURFACE_CONTAINER_HIGH)
            if entering
            else None
        )
        safe_update(self)


class ChipGroup(ft.Container):
    """A group of exclusive chips inside a padded tonal track."""

    def __init__(
        self,
        options: list[str],
        value: str | None = None,
        on_change: Callable[[str], None] | None = None,
        columns: int | None = None,
        sublabels: dict[str, str] | None = None,
        accent: str = ft.Colors.PRIMARY,
        expand: bool | int | None = None,
    ) -> None:
        self._options = list(options)
        self.value: str | None = (
            value if value is not None else (self._options[0] if self._options else None)
        )
        self._on_change = on_change
        self._accent = accent
        self._chips: dict[str, _Chip] = {}

        sublabels = sublabels or {}
        for opt in self._options:
            self._chips[opt] = _Chip(opt, sublabels.get(opt), self._make_handler(opt))

        if columns:
            rows: list[ft.Control] = []
            chip_list = list(self._chips.values())
            for i in range(0, len(chip_list), columns):
                row_chips = chip_list[i : i + columns]
                for chip in row_chips:
                    chip.expand = True
                # Pad the last row so cells keep equal widths.
                fillers: list[ft.Control] = [
                    ft.Container(expand=True) for _ in range(columns - len(row_chips))
                ]
                rows.append(ft.Row([*row_chips, *fillers], spacing=4))
            layout: ft.Control = ft.Column(rows, spacing=4)
        else:
            for chip in self._chips.values():
                chip.expand = True
            layout = ft.Row(list(self._chips.values()), spacing=4)

        super().__init__(
            content=layout,
            padding=4,
            expand=expand,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
        )
        self._style()

    def _make_handler(self, option: str):
        def handler(e: ft.Event) -> None:
            if option == self.value:
                return
            self.value = option
            self._style()
            safe_update(self)
            if self._on_change:
                self._on_change(option)

        return handler

    def set_value(self, value: str) -> None:
        if value in self._chips:
            self.value = value
            self._style()
            safe_update(self)

    def _style(self) -> None:
        for opt, chip in self._chips.items():
            selected = opt == self.value
            chip.selected = selected
            chip.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH if selected else None
            chip.border = ft.Border.all(
                1, self._accent if selected else ft.Colors.TRANSPARENT
            )
            chip.label_text.color = (
                self._accent if selected else ft.Colors.ON_SURFACE
            )
            chip.label_text.weight = (
                ft.FontWeight.W_600 if selected else ft.FontWeight.W_500
            )
