"""Per-download tile: thumbnail, state pill, progress bar/overlay and actions.

The card background itself fills left-to-right with a tinted overlay that
tracks download progress (coral while downloading, teal while ffmpeg runs).
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.models.download import (
    DownloadMode,
    DownloadState,
    DownloadTask,
    ProgressInfo,
)
from video_downloader.ui import theme
from video_downloader.ui.components.status_pill import (
    PILL_CORAL,
    PILL_GREEN,
    PILL_TEAL,
    STATE_PILL_COLORS,
    StatusPill,
)
from video_downloader.ui.texts import STATE_LABELS, t
from video_downloader.utils.formatting import human_bytes, human_eta, human_speed

_BAR_COLORS: dict[DownloadState, str] = {
    DownloadState.DOWNLOADING: PILL_CORAL,
    DownloadState.PROCESSING: PILL_TEAL,
    DownloadState.PREPARING: PILL_CORAL,
    DownloadState.COMPLETED: PILL_GREEN,
}


class DownloadTile(ft.Container):
    def __init__(
        self,
        task: DownloadTask,
        on_cancel: Callable[[str], None],
        on_retry: Callable[[str], None],
        on_open_folder: Callable[[str], None],
    ) -> None:
        super().__init__(
            padding=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
        )
        self.task = task
        self._on_cancel = on_cancel
        self._on_retry = on_retry
        self._on_open_folder = on_open_folder

        self._thumb = self._build_thumbnail()
        self._title = ft.Text(
            task.request.title or task.request.url,
            weight=ft.FontWeight.W_600,
            size=15,
            color=ft.Colors.ON_SURFACE,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
        self._pill = StatusPill()
        self._progress = ft.ProgressBar(
            value=0,
            height=8,
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
            color=PILL_CORAL,
        )
        self._stats = ft.Text(
            style=theme.data_style(ft.Colors.ON_SURFACE_VARIANT),
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._error = ft.Text(
            size=12, color=ft.Colors.ERROR, visible=False, max_lines=2
        )

        self._cancel_btn = ft.IconButton(
            ft.Icons.CLOSE,
            tooltip=t("cancel"),
            icon_size=20,
            on_click=lambda e: self._on_cancel(self.task.id),
        )
        self._retry_btn = ft.IconButton(
            ft.Icons.REFRESH,
            tooltip=t("retry"),
            icon_size=20,
            visible=False,
            on_click=lambda e: self._on_retry(self.task.id),
        )
        self._folder_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            tooltip=t("open_folder"),
            icon_size=20,
            visible=False,
            on_click=lambda e: self._on_open_folder(self.task.id),
        )

        self.content = ft.Row(
            [
                self._thumb,
                ft.Column(
                    [
                        ft.Row(
                            [self._title, self._pill],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        self._progress,
                        self._stats,
                        self._error,
                    ],
                    spacing=7,
                    expand=True,
                ),
                ft.Row(
                    [self._cancel_btn, self._retry_btn, self._folder_btn],
                    spacing=0,
                ),
            ],
            spacing=14,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        self.refresh()

    # ------------------------------------------------------------------

    def _build_thumbnail(self) -> ft.Control:
        url = self.task.request.thumbnail_url
        if url:
            return ft.Container(
                content=ft.Image(
                    src=url, width=96, height=54, fit=ft.BoxFit.COVER
                ),
                border_radius=ft.BorderRadius.all(8),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        icon = (
            ft.Icons.MUSIC_NOTE
            if self.task.request.mode is DownloadMode.AUDIO_ONLY
            else ft.Icons.MOVIE
        )
        return ft.Container(
            content=ft.Icon(
                icon, size=22, color=ft.Colors.ON_SURFACE_VARIANT, opacity=0.6
            ),
            width=96,
            height=54,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=ft.BorderRadius.all(8),
        )

    def _set_overlay(self, fraction: float | None, color: str | None) -> None:
        """Tint the card background up to `fraction` of its width."""
        if color is None or fraction is None or fraction <= 0:
            self.gradient = None
            return
        fill = ft.Colors.with_opacity(0.08, color)
        p = min(max(fraction, 0.0), 1.0)
        self.gradient = ft.LinearGradient(
            begin=ft.Alignment.CENTER_LEFT,
            end=ft.Alignment.CENTER_RIGHT,
            colors=[fill, fill, ft.Colors.TRANSPARENT, ft.Colors.TRANSPARENT],
            stops=[0, p, p, 1],
        )

    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Sync every visual element from the bound task (no .update())."""
        task = self.task
        state = task.state

        self._pill.set_state(STATE_LABELS[state], STATE_PILL_COLORS[state])
        self._progress.color = _BAR_COLORS.get(state, PILL_CORAL)

        if state is DownloadState.DOWNLOADING:
            self._apply_progress(task.progress)
        elif state in (DownloadState.PREPARING, DownloadState.PENDING):
            self._progress.value = None if state is DownloadState.PREPARING else 0
            self._stats.value = STATE_LABELS[state]
            self._set_overlay(None, None)
        elif state is DownloadState.PROCESSING:
            self._progress.value = None
            self._stats.value = STATE_LABELS[state]
            self._set_overlay(1.0, PILL_TEAL)
        elif state is DownloadState.COMPLETED:
            self._progress.value = 1
            self._stats.value = str(task.output_path) if task.output_path else ""
            self._set_overlay(None, None)
        elif state is DownloadState.ERROR or state is DownloadState.CANCELLED:
            self._progress.value = 0
            self._stats.value = ""
            self._set_overlay(None, None)

        self._error.visible = state is DownloadState.ERROR and bool(task.error)
        if self._error.visible:
            self._error.value = t(task.error or "error_generic")

        self._cancel_btn.visible = task.is_active
        self._retry_btn.visible = state in (DownloadState.ERROR, DownloadState.CANCELLED)
        self._folder_btn.visible = state is DownloadState.COMPLETED

    def set_progress(self, progress: ProgressInfo) -> None:
        self.task.progress = progress
        if self.task.state is DownloadState.DOWNLOADING:
            self._apply_progress(progress)

    def set_processing(self, processor: str) -> None:
        self._stats.value = f"{STATE_LABELS[DownloadState.PROCESSING]} ({processor})"

    # ------------------------------------------------------------------

    def _apply_progress(self, progress: ProgressInfo) -> None:
        percent = progress.percent
        self._progress.value = percent  # None -> indeterminate
        self._set_overlay(percent, PILL_CORAL)
        downloaded = human_bytes(progress.downloaded_bytes)
        total = human_bytes(progress.total_bytes, approx=progress.total_is_estimate)
        parts = []
        if percent is not None:
            parts.append(f"{percent * 100:.0f} %")
        parts.append(f"{downloaded} / {total}")
        parts.append(f"{t('speed')}: {human_speed(progress.speed_bps)}")
        parts.append(f"{t('eta')}: {human_eta(progress.eta_seconds)}")
        self._stats.value = "   ·   ".join(parts)
