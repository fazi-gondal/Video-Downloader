"""Download mode selector cards and labeled option dropdowns."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.models.download import DownloadMode
from video_downloader.ui import theme
from video_downloader.ui.texts import t
from video_downloader.ui.utils import safe_update

_MODES: list[tuple[DownloadMode, str, str, ft.IconData]] = [
    (
        DownloadMode.VIDEO_AUDIO,
        "mode_video_audio",
        "mode_video_audio_desc",
        ft.Icons.SMART_DISPLAY,
    ),
    (DownloadMode.VIDEO_ONLY, "mode_video", "mode_video_desc", ft.Icons.VIDEOCAM),
    (DownloadMode.AUDIO_ONLY, "mode_audio", "mode_audio_desc", ft.Icons.MUSIC_NOTE),
]


class ModeSelector(ft.Row):
    """Three selectable cards, one per download mode."""

    def __init__(
        self,
        value: DownloadMode = DownloadMode.VIDEO_AUDIO,
        on_change: Callable[[DownloadMode], None] | None = None,
    ) -> None:
        super().__init__()
        self.value = value
        self._on_change = on_change
        self._cards: dict[DownloadMode, ft.Container] = {}
        self._icons: dict[DownloadMode, ft.Icon] = {}
        self.spacing = 12

        for mode, label_key, desc_key, icon in _MODES:
            icon_ctl = ft.Icon(icon, size=30)
            card = ft.Container(
                content=ft.Column(
                    [
                        icon_ctl,
                        ft.Text(
                            t(label_key),
                            size=14.5,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.ON_SURFACE,
                        ),
                        ft.Text(
                            t(desc_key),
                            size=11.5,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    spacing=6,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(vertical=20, horizontal=14),
                border_radius=ft.BorderRadius.all(theme.RADIUS_CARD - 4),
                expand=True,
                alignment=ft.Alignment.CENTER,
                on_click=self._make_handler(mode),
                ink=True,
            )
            self._cards[mode] = card
            self._icons[mode] = icon_ctl
            self.controls.append(card)
        self._style_cards()

    def _make_handler(self, mode: DownloadMode):
        def handler(e: ft.Event) -> None:
            self.value = mode
            self._style_cards()
            if self._on_change:
                self._on_change(mode)
            safe_update(self)

        return handler

    def _style_cards(self) -> None:
        for mode, card in self._cards.items():
            selected = mode is self.value
            card.bgcolor = ft.Colors.PRIMARY_CONTAINER if selected else (
                ft.Colors.SURFACE_CONTAINER_LOW
            )
            card.border = ft.Border.all(
                1.5 if selected else 1,
                ft.Colors.PRIMARY if selected else ft.Colors.OUTLINE_VARIANT,
            )
            self._icons[mode].color = (
                ft.Colors.PRIMARY if selected else ft.Colors.ON_SURFACE_VARIANT
            )


def labeled_dropdown(
    label: str,
    options: list[str],
    value: str | None = None,
    on_select: Callable[[ft.Event], None] | None = None,
    width: int = 220,
) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        options=[ft.DropdownOption(key=opt, text=opt) for opt in options],
        value=value if value is not None else (options[0] if options else None),
        on_select=on_select,
        width=width,
    )
