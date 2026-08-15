"""Centered empty-state placeholder used by lists (downloads, history, jobs)."""

from __future__ import annotations

import flet as ft


class EmptyState(ft.Container):
    def __init__(
        self,
        icon: ft.IconData,
        title: str,
        subtitle: str | None = None,
        compact: bool = False,
    ) -> None:
        texts: list[ft.Control] = [
            ft.Text(
                title,
                size=15,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            )
        ]
        if subtitle:
            texts.append(
                ft.Text(
                    subtitle,
                    size=13,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    opacity=0.7,
                    text_align=ft.TextAlign.CENTER,
                )
            )
        super().__init__(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(
                            icon, size=40, color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                        width=72,
                        height=72,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                        border_radius=ft.BorderRadius.all(999),
                        opacity=0.8,
                    ),
                    *texts,
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.symmetric(vertical=16 if compact else 48, horizontal=16),
        )
