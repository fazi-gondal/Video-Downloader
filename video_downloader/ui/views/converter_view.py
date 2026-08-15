"""Post-download file conversion: remux or re-encode local files.

Teal-accented module: 7/5 grid with the source/options column on the left
and the live job queue on the right.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import flet as ft

from video_downloader.config.constants import (
    AUDIO_FORMATS,
    CONVERSION_VIDEO_CONTAINERS,
)
from video_downloader.core.events import (
    ConversionFinished,
    ConversionProgress,
    ConversionQueued,
)
from video_downloader.models.conversion import ConversionMode, ConversionRequest, MediaKind
from video_downloader.ui import theme
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.buttons import secondary_button, teal_button
from video_downloader.ui.components.chip_group import ChipGroup
from video_downloader.ui.components.empty_state import EmptyState
from video_downloader.ui.components.status_pill import (
    PILL_AMBER,
    PILL_GREEN,
    PILL_TEAL,
    StatusPill,
)
from video_downloader.ui.texts import t
from video_downloader.ui.utils import run_task, safe_update
from video_downloader.utils.paths import open_in_file_manager

_AUDIO_EXTENSIONS = {"mp3", "m4a", "aac", "flac", "opus", "wav", "ogg", "wma"}
_MEDIA_EXTENSIONS = sorted(
    _AUDIO_EXTENSIONS | {"mp4", "mkv", "webm", "avi", "mov", "flv", "ts", "m4v"}
)


def _section_title(text: str) -> ft.Text:
    return ft.Text(text, style=theme.headline_md())


class _JobTile(ft.Container):
    def __init__(self, title: str, on_cancel) -> None:
        super().__init__(
            padding=14,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
        )
        self.output_path: Path | None = None
        self._title = ft.Text(
            title,
            weight=ft.FontWeight.W_600,
            size=14,
            color=ft.Colors.ON_SURFACE,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.progress = ft.ProgressBar(
            value=None,
            height=8,
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
            color=PILL_TEAL,
        )
        self.status = ft.Text(
            style=theme.data_style(ft.Colors.ON_SURFACE_VARIANT),
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.cancel_btn = ft.IconButton(
            ft.Icons.CLOSE, tooltip=t("cancel"), icon_size=20, on_click=on_cancel
        )
        self.folder_btn = ft.IconButton(
            ft.Icons.FOLDER_OPEN,
            tooltip=t("open_folder"),
            icon_size=20,
            visible=False,
            on_click=self._open_folder,
        )
        self.content = ft.Row(
            [
                ft.Icon(
                    ft.Icons.SWAP_HORIZ, size=20, color=ft.Colors.SECONDARY
                ),
                ft.Column(
                    [self._title, self.progress, self.status], spacing=6, expand=True
                ),
                self.cancel_btn,
                self.folder_btn,
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _open_folder(self, e: ft.Event) -> None:
        if self.output_path:
            open_in_file_manager(self.output_path)


class ConverterView(ft.Column):
    def __init__(self, ctx: AppContext) -> None:
        super().__init__()
        self.ctx = ctx
        self.expand = True
        self.spacing = 16

        self._source: Path | None = None
        self._can_remux: bool | None = None
        self._tiles: dict[str, _JobTile] = {}
        self._picker = ft.FilePicker()

        # --- Source drop-style zone ----------------------------------------
        self._file_text = ft.Text(
            t("converter_drop_hint"),
            color=ft.Colors.ON_SURFACE_VARIANT,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
            text_align=ft.TextAlign.CENTER,
        )
        self._drop_zone = ft.Container(
            content=ft.Column(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.UPLOAD_FILE, size=28, color=ft.Colors.SECONDARY
                        ),
                        width=64,
                        height=64,
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.SECONDARY_CONTAINER,
                        border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
                    ),
                    self._file_text,
                    secondary_button(
                        t("pick_file"),
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=self._pick_file,
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            height=210,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
            on_click=self._pick_file,
            ink=True,
        )

        # --- Output options ---------------------------------------------------
        self._video_cg = ChipGroup(
            CONVERSION_VIDEO_CONTAINERS,
            accent=ft.Colors.SECONDARY,
            on_change=self._on_target_change,
        )
        self._audio_cg = ChipGroup(
            AUDIO_FORMATS,
            accent=ft.Colors.SECONDARY,
            on_change=self._on_target_change,
        )
        self._audio_cg.visible = False

        self._badge = StatusPill()
        self._badge.visible = False
        self._keep_cb = ft.Checkbox(
            label=t("keep_original"), value=ctx.settings.keep_originals
        )
        self._convert_btn = teal_button(
            t("convert"),
            icon=ft.Icons.PLAY_ARROW,
            disabled=True,
            on_click=self._on_convert,
        )

        options_card = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.TUNE, size=18, color=ft.Colors.SECONDARY),
                            _section_title(t("target_format")),
                            self._badge,
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    self._video_cg,
                    self._audio_cg,
                    ft.Row(
                        [self._keep_cb, ft.Container(expand=True), self._convert_btn],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=14,
            ),
            padding=18,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
        )

        # --- Job queue --------------------------------------------------------
        self._jobs_empty = EmptyState(
            ft.Icons.INBOX_OUTLINED, t("no_conversions"), compact=True
        )
        self._jobs_list = ft.Column(spacing=10)

        ffmpeg_warning = ft.Container(
            visible=not ctx.ffmpeg.is_available,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.4, ft.Colors.ERROR)),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
            padding=12,
            content=ft.Text(t("ffmpeg_missing"), color=ft.Colors.ERROR),
        )

        left = ft.Column(
            [
                _section_title(t("converter_source")),
                self._drop_zone,
                options_card,
            ],
            spacing=14,
            expand=7,
        )
        right = ft.Column(
            [
                _section_title(t("converter_queue")),
                self._jobs_empty,
                self._jobs_list,
            ],
            spacing=14,
            expand=5,
            scroll=ft.ScrollMode.AUTO,
        )

        self.controls = [
            ft.Text(t("converter_title"), style=theme.headline_xl()),
            ffmpeg_warning,
            ft.Row(
                [left, right],
                spacing=24,
                expand=True,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        ]

        bus = ctx.bus
        bus.subscribe(ConversionQueued, self._on_queued)
        bus.subscribe(ConversionProgress, self._on_progress)
        bus.subscribe(ConversionFinished, self._on_finished)

    def did_mount(self) -> None:
        if self._picker not in self.page.services:
            self.page.services.append(self._picker)

    # ------------------------------------------------------------------

    @property
    def _kind(self) -> MediaKind:
        if self._source and self._source.suffix.lstrip(".").lower() in _AUDIO_EXTENSIONS:
            return MediaKind.AUDIO
        return MediaKind.VIDEO

    @property
    def _target(self) -> str:
        cg = self._audio_cg if self._kind is MediaKind.AUDIO else self._video_cg
        return cg.value or ""

    async def _pick_file(self, e: ft.Event) -> None:
        files = await self._picker.pick_files(
            dialog_title=t("pick_file"),
            allowed_extensions=_MEDIA_EXTENSIONS,
        )
        if not files or not files[0].path:
            return
        self._source = Path(files[0].path)
        self._file_text.value = str(self._source)
        self._file_text.color = ft.Colors.ON_SURFACE
        is_audio = self._kind is MediaKind.AUDIO
        self._audio_cg.visible = is_audio
        self._video_cg.visible = not is_audio
        self._convert_btn.disabled = not self.ctx.ffmpeg.is_available
        self.update()
        await self._refresh_badge()

    def _on_target_change(self, value: str) -> None:
        if self._source is None:
            return
        run_task(self, self._refresh_badge)

    async def _refresh_badge(self) -> None:
        if self._source is None:
            return
        if self._kind is MediaKind.AUDIO:
            # Audio conversion always re-encodes (except same-format copy)
            self._can_remux = False
            remux = False
        else:
            self._can_remux = await asyncio.to_thread(
                self.ctx.ffmpeg.can_remux, self._source, self._target
            )
            remux = self._can_remux
        self._badge.set_state(
            t("remux_badge") if remux else t("reencode_badge"),
            PILL_GREEN if remux else PILL_AMBER,
        )
        self._badge.visible = True
        self.update()

    # ------------------------------------------------------------------

    def _on_convert(self, e: ft.Event) -> None:
        if self._source is None or not self._target:
            return
        kind = self._kind
        mode = (
            ConversionMode.REMUX
            if kind is MediaKind.VIDEO and self._can_remux
            else ConversionMode.REENCODE
        )
        request = ConversionRequest(
            source=self._source,
            target_format=self._target,
            kind=kind,
            mode=mode,
            keep_original=bool(self._keep_cb.value),
        )
        self.ctx.conversions.enqueue(request)

    # ------------------------------------------------------------------
    # Event handlers (UI loop)

    def _on_queued(self, event: ConversionQueued) -> None:
        job = self.ctx.conversions.get(event.task_id)
        if job is None or event.task_id in self._tiles:
            return
        tile = _JobTile(
            f"{job.request.source.name}  →  {job.request.target_format}",
            on_cancel=lambda e, jid=event.task_id: self.ctx.conversions.cancel(jid),
        )
        self._tiles[event.task_id] = tile
        self._jobs_list.controls.insert(0, tile)
        self._jobs_empty.visible = False
        safe_update(self)

    def _on_progress(self, event: ConversionProgress) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.progress.value = event.percent
        if event.percent is not None:
            tile.status.value = f"{event.percent * 100:.0f} %"
        safe_update(self)

    def _on_finished(self, event: ConversionFinished) -> None:
        tile = self._tiles.get(event.task_id)
        if tile is None:
            return
        tile.cancel_btn.visible = False
        if event.error_key:
            tile.progress.value = 0
            tile.status.value = t(event.error_key)
            tile.status.color = ft.Colors.ERROR
        elif event.output_path:
            tile.progress.value = 1
            tile.progress.color = PILL_GREEN
            tile.status.value = f"{t('conversion_done')}: {event.output_path}"
            tile.output_path = event.output_path
            tile.folder_btn.visible = True
        else:  # cancelled
            tile.progress.value = 0
            tile.status.value = t("state_cancelled")
        safe_update(self)
