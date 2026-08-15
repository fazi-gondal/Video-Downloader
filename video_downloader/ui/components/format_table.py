"""Table of available formats with optional row selection.

Selection semantics: clicking a row marks it as the chosen video stream
(video/muxed rows) or audio stream (audio rows) for manual downloads.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from video_downloader.models.media import FormatInfo, StreamType
from video_downloader.ui import theme
from video_downloader.ui.components.status_pill import (
    PILL_BLUE,
    PILL_CORAL,
    PILL_GREEN,
    StatusPill,
)
from video_downloader.ui.texts import t
from video_downloader.utils.formatting import human_bitrate, human_bytes, human_fps

_TYPE_LABELS = {
    StreamType.VIDEO_ONLY: "stream_video",
    StreamType.AUDIO_ONLY: "stream_audio",
    StreamType.MUXED: "stream_muxed",
}
_TYPE_COLORS = {
    StreamType.VIDEO_ONLY: PILL_BLUE,
    StreamType.AUDIO_ONLY: PILL_GREEN,
    StreamType.MUXED: PILL_CORAL,
}


def _heading(text: str) -> ft.Text:
    return ft.Text(text, color=ft.Colors.ON_SURFACE_VARIANT)


class FormatTable(ft.Column):
    def __init__(
        self,
        formats: list[FormatInfo],
        selectable: bool = False,
        on_selection: Callable[[FormatInfo | None, FormatInfo | None], None] | None = None,
    ) -> None:
        super().__init__()
        self._formats = formats
        self._selectable = selectable
        self._on_selection = on_selection
        self.selected_video: FormatInfo | None = None
        self.selected_audio: FormatInfo | None = None
        self._rows: dict[str, ft.DataRow] = {}

        table = ft.DataTable(
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL + 2),
            horizontal_lines=ft.BorderSide(
                1, ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT)
            ),
            columns=[
                ft.DataColumn(label=_heading(t("fmt_id"))),
                ft.DataColumn(label=_heading(t("fmt_ext"))),
                ft.DataColumn(label=_heading(t("fmt_resolution"))),
                ft.DataColumn(label=_heading(t("fmt_fps")), numeric=True),
                ft.DataColumn(label=_heading(t("fmt_vcodec"))),
                ft.DataColumn(label=_heading(t("fmt_acodec"))),
                ft.DataColumn(label=_heading(t("fmt_bitrate")), numeric=True),
                ft.DataColumn(label=_heading(t("fmt_size")), numeric=True),
                ft.DataColumn(label=_heading(t("fmt_type"))),
            ],
            heading_row_height=44,
            data_row_min_height=40,
            data_row_max_height=48,
            column_spacing=18,
        )
        for f in formats:
            row = ft.DataRow(
                cells=[
                    ft.DataCell(
                        ft.Text(
                            f.format_id,
                            font_family="monospace",
                            size=12,
                            color=ft.Colors.ON_SURFACE,
                        )
                    ),
                    ft.DataCell(ft.Text(f.ext, color=ft.Colors.ON_SURFACE)),
                    ft.DataCell(ft.Text(f.resolution or "—", color=ft.Colors.ON_SURFACE)),
                    ft.DataCell(ft.Text(human_fps(f.fps), color=ft.Colors.ON_SURFACE)),
                    ft.DataCell(ft.Text(f.vcodec or "—", size=12, color=ft.Colors.ON_SURFACE)),
                    ft.DataCell(ft.Text(f.acodec or "—", size=12, color=ft.Colors.ON_SURFACE)),
                    ft.DataCell(ft.Text(human_bitrate(f.tbr or f.abr), color=ft.Colors.ON_SURFACE)),
                    ft.DataCell(
                        ft.Text(
                            human_bytes(f.filesize, approx=f.filesize_is_approx),
                            color=ft.Colors.ON_SURFACE,
                        )
                    ),
                    ft.DataCell(
                        StatusPill(
                            t(_TYPE_LABELS[f.stream_type]),
                            _TYPE_COLORS[f.stream_type],
                        )
                    ),
                ],
            )
            if selectable:
                row.on_select_change = self._make_select_handler(f, row)
            self._rows[f.format_id] = row
            table.rows.append(row)

        self.controls = [
            ft.Row([table], scroll=ft.ScrollMode.AUTO),
        ]

    # ------------------------------------------------------------------

    def _make_select_handler(self, fmt: FormatInfo, row: ft.DataRow):
        def handler(e: ft.Event) -> None:
            if fmt.stream_type is StreamType.AUDIO_ONLY:
                previous = self.selected_audio
                self.selected_audio = None if previous is fmt else fmt
                self._sync_selection(StreamType.AUDIO_ONLY)
            else:
                previous = self.selected_video
                self.selected_video = None if previous is fmt else fmt
                self._sync_selection(StreamType.VIDEO_ONLY)
            if self._on_selection:
                self._on_selection(self.selected_video, self.selected_audio)
            self.update()

        return handler

    def _sync_selection(self, kind: StreamType) -> None:
        for f in self._formats:
            row = self._rows[f.format_id]
            if kind is StreamType.AUDIO_ONLY and f.stream_type is StreamType.AUDIO_ONLY:
                row.selected = f is self.selected_audio
            elif kind is not StreamType.AUDIO_ONLY and f.stream_type is not StreamType.AUDIO_ONLY:
                row.selected = f is self.selected_video
