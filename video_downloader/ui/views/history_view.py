"""Download history with filters, search, re-download and cleanup actions."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft

from video_downloader.models.download import DownloadMode, DownloadRequest, DownloadState
from video_downloader.services.history_service import HistoryEntry
from video_downloader.ui import theme
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.buttons import secondary_button
from video_downloader.ui.components.empty_state import EmptyState
from video_downloader.ui.components.status_pill import (
    PILL_GREY,
    STATE_PILL_COLORS,
    StatusPill,
)
from video_downloader.ui.texts import STATE_LABELS, t
from video_downloader.ui.utils import safe_update
from video_downloader.utils.paths import open_in_file_manager

_FILTERS: list[tuple[str, str]] = [
    ("all", "history_filter_all"),
    ("video", "history_filter_video"),
    ("audio", "history_filter_audio"),
    ("error", "history_filter_error"),
]


class _FilterPill(ft.Container):
    def __init__(self, label: str, on_click: Callable) -> None:
        super().__init__(
            content=ft.Text(label, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
            padding=ft.Padding.symmetric(vertical=6, horizontal=16),
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
            border=ft.Border.all(1, ft.Colors.TRANSPARENT),
            on_click=on_click,
        )

    def set_active(self, active: bool) -> None:
        text = self.content
        assert isinstance(text, ft.Text)
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGH if active else None
        self.border = ft.Border.all(
            1, ft.Colors.OUTLINE if active else ft.Colors.TRANSPARENT
        )
        text.color = ft.Colors.ON_SURFACE if active else ft.Colors.ON_SURFACE_VARIANT
        text.weight = ft.FontWeight.W_600 if active else ft.FontWeight.W_400


class HistoryView(ft.Column):
    def __init__(self, ctx: AppContext, on_redownload: Callable[[], None]) -> None:
        super().__init__()
        self.ctx = ctx
        self.on_redownload = on_redownload
        self.expand = True
        self.spacing = 14

        self._all_entries: list[HistoryEntry] = []
        self._filter = "all"

        self._empty = EmptyState(ft.Icons.HISTORY, t("no_history"))
        self._no_results = EmptyState(
            ft.Icons.SEARCH_OFF, t("no_results"), compact=True
        )
        self._no_results.visible = False
        self._list = ft.ListView(spacing=8, expand=True)

        self._search_field = ft.TextField(
            hint_text=t("history_search_hint"),
            expand=True,
            border=ft.InputBorder.NONE,
            text_style=theme.body_md(),
            on_change=lambda e: self._apply_filters(),
        )
        search_bar = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.SEARCH,
                            size=18,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        padding=ft.Padding(left=12, top=0, right=0, bottom=0),
                    ),
                    self._search_field,
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            width=320,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
        )

        self._filter_pills: dict[str, _FilterPill] = {
            key: _FilterPill(t(label_key), self._make_filter_handler(key))
            for key, label_key in _FILTERS
        }
        self._style_filters()

        clear_button = secondary_button(
            t("clear_finished"),
            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
            on_click=self._on_clear,
        )

        self.controls = [
            ft.Row(
                [
                    ft.Text(t("history_title"), style=theme.headline_xl()),
                    clear_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Row(
                [
                    ft.Row(list(self._filter_pills.values()), spacing=6),
                    ft.Container(expand=True),
                    search_bar,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            self._empty,
            self._no_results,
            self._list,
        ]

    def did_mount(self) -> None:
        self.reload()

    # ------------------------------------------------------------------

    def reload(self) -> None:
        self._all_entries = self.ctx.history.list_entries()
        self._apply_filters()

    def _make_filter_handler(self, key: str):
        def handler(e: ft.Event) -> None:
            self._filter = key
            self._style_filters()
            self._apply_filters()

        return handler

    def _style_filters(self) -> None:
        for key, pill in self._filter_pills.items():
            pill.set_active(key == self._filter)

    def _matches(self, entry: HistoryEntry) -> bool:
        if self._filter == "video" and entry.mode == DownloadMode.AUDIO_ONLY.value:
            return False
        if self._filter == "audio" and entry.mode != DownloadMode.AUDIO_ONLY.value:
            return False
        if self._filter == "error" and entry.state != DownloadState.ERROR.value:
            return False
        query = (self._search_field.value or "").strip().lower()
        if query:
            haystack = f"{entry.title} {entry.url}".lower()
            if query not in haystack:
                return False
        return True

    def _apply_filters(self) -> None:
        filtered = [entry for entry in self._all_entries if self._matches(entry)]
        self._list.controls = [self._make_row(entry) for entry in filtered]
        self._empty.visible = not self._all_entries
        self._no_results.visible = bool(self._all_entries) and not filtered
        safe_update(self)

    # ------------------------------------------------------------------

    def _make_row(self, entry: HistoryEntry) -> ft.Control:
        state_label = STATE_LABELS.get(DownloadState(entry.state), entry.state)
        pill_color = STATE_PILL_COLORS.get(DownloadState(entry.state), PILL_GREY)
        pill = StatusPill(state_label, pill_color)

        actions = ft.Row(
            [
                ft.IconButton(
                    ft.Icons.DOWNLOAD,
                    tooltip=t("redownload"),
                    icon_size=20,
                    on_click=lambda e, en=entry: self._redownload(en),
                ),
                ft.IconButton(
                    ft.Icons.FOLDER_OPEN,
                    tooltip=t("open_folder"),
                    icon_size=20,
                    visible=bool(entry.output_path),
                    on_click=lambda e, en=entry: self._open_folder(en),
                ),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE,
                    tooltip=t("delete_entry"),
                    icon_size=20,
                    on_click=lambda e, en=entry: self._delete(en),
                ),
            ],
            spacing=0,
        )
        is_audio = entry.mode == DownloadMode.AUDIO_ONLY.value
        leading = ft.Container(
            content=ft.Icon(
                ft.Icons.MUSIC_NOTE if is_audio else ft.Icons.MOVIE,
                size=20,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            width=44,
            height=44,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=ft.BorderRadius.all(10),
        )

        row = ft.Container(
            padding=ft.Padding(left=12, top=8, right=6, bottom=8),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD - 4),
            content=ft.Row(
                [
                    leading,
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(
                                        entry.title,
                                        weight=ft.FontWeight.W_600,
                                        size=14,
                                        color=ft.Colors.ON_SURFACE,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        expand=True,
                                    ),
                                    pill,
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Text(
                                f"{entry.created_at.replace('T', ' ')} · {entry.url}",
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=3,
                        expand=True,
                    ),
                    actions,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            on_hover=self._on_row_hover,
        )
        return row

    def _on_row_hover(self, e: ft.Event) -> None:
        entering = e.data is True or e.data == "true"
        e.control.bgcolor = (
            ft.Colors.SURFACE_CONTAINER_HIGH
            if entering
            else ft.Colors.SURFACE_CONTAINER_LOW
        )
        safe_update(e.control)

    # ------------------------------------------------------------------

    def _redownload(self, entry: HistoryEntry) -> None:
        request = DownloadRequest(
            url=entry.url,
            title=entry.title,
            mode=DownloadMode(entry.mode),
            output_dir=Path(entry.output_dir),
            container=entry.container or "mp4",
            audio_format=entry.audio_format or "mp3",
            embed_metadata=self.ctx.settings.embed_metadata,
            embed_thumbnail=self.ctx.settings.embed_thumbnail,
        )
        self.ctx.download_manager.enqueue(request)
        self.on_redownload()

    def _open_folder(self, entry: HistoryEntry) -> None:
        if entry.output_path:
            open_in_file_manager(Path(entry.output_path))

    def _delete(self, entry: HistoryEntry) -> None:
        self.ctx.history.delete(entry.id)
        self.reload()

    def _on_clear(self, e: ft.Event) -> None:
        self.ctx.history.clear()
        self.reload()
