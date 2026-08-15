"""Active/finished downloads list, live-updated from EventBus events."""

from __future__ import annotations

import flet as ft

from video_downloader.core.events import (
    TaskPostProcessing,
    TaskProgress,
    TaskQueued,
    TaskStateChanged,
)
from video_downloader.models.download import DownloadState
from video_downloader.ui import theme
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.buttons import secondary_button
from video_downloader.ui.components.download_tile import DownloadTile
from video_downloader.ui.components.empty_state import EmptyState
from video_downloader.ui.texts import t
from video_downloader.ui.utils import safe_update
from video_downloader.utils.paths import open_in_file_manager

_ACTIVE_STATES = (
    DownloadState.PREPARING,
    DownloadState.DOWNLOADING,
    DownloadState.PROCESSING,
)


class DownloadsView(ft.Column):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.expand = True
        self.spacing = 16
        self._tiles: dict[str, DownloadTile] = {}

        self._summary = ft.Text(
            "", style=theme.body_sm(ft.Colors.ON_SURFACE_VARIANT)
        )
        self._empty = EmptyState(
            ft.Icons.DOWNLOAD_OUTLINED,
            t("no_downloads"),
            t("no_downloads_hint"),
        )
        self._list = ft.ListView(spacing=10, expand=True)
        self._clear_button = secondary_button(
            t("clear_finished"),
            icon=ft.Icons.DELETE_SWEEP_OUTLINED,
            on_click=self._on_clear_finished,
        )

        self.controls = [
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(t("downloads_title"), style=theme.headline_xl()),
                            self._summary,
                        ],
                        spacing=2,
                    ),
                    self._clear_button,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            self._empty,
            self._list,
        ]
        self._refresh_summary()

        bus = ctx.bus
        bus.subscribe(TaskQueued, self._on_queued)
        bus.subscribe(TaskStateChanged, self._on_state_changed)
        bus.subscribe(TaskProgress, self._on_progress)
        bus.subscribe(TaskPostProcessing, self._on_postprocessing)

    # ------------------------------------------------------------------
    # Event handlers (always run on the UI loop via the EventBus pump)

    def _on_queued(self, event: TaskQueued) -> None:
        task = self.ctx.download_manager.get(event.task_id)
        if task is None or event.task_id in self._tiles:
            return
        tile = DownloadTile(
            task,
            on_cancel=self.ctx.download_manager.cancel,
            on_retry=self._retry,
            on_open_folder=self._open_folder,
        )
        self._tiles[event.task_id] = tile
        self._list.controls.insert(0, tile)
        self._empty.visible = False
        self._refresh_summary()
        safe_update(self)

    def _on_state_changed(self, event: TaskStateChanged) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.refresh()
        self._refresh_summary()
        safe_update(self)

    def _on_progress(self, event: TaskProgress) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.set_progress(event.progress)
        safe_update(self)

    def _on_postprocessing(self, event: TaskPostProcessing) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.set_processing(event.processor)
        safe_update(self)

    # ------------------------------------------------------------------

    def _refresh_summary(self) -> None:
        tasks = self.ctx.download_manager.tasks()
        active = sum(1 for task in tasks if task.state in _ACTIVE_STATES)
        queued = sum(1 for task in tasks if task.state is DownloadState.PENDING)
        self._summary.value = (
            f"{active} {t('active_label')} · {queued} {t('queued_label')}"
        )

    def _retry(self, task_id: str) -> None:
        self.ctx.download_manager.retry(task_id)

    def _open_folder(self, task_id: str) -> None:
        task = self.ctx.download_manager.get(task_id)
        if task and task.output_path:
            open_in_file_manager(task.output_path)

    def _on_clear_finished(self, e: ft.Event) -> None:
        self.ctx.download_manager.clear_finished()
        for task_id in list(self._tiles):
            tile = self._tiles[task_id]
            if tile.task.is_terminal:
                self._list.controls.remove(tile)
                del self._tiles[task_id]
        self._empty.visible = not self._tiles
        self._refresh_summary()
        safe_update(self)
