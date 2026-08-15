"""Destination folder selector backed by the native directory dialog."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import flet as ft

from video_downloader.ui.texts import t


class FolderPicker(ft.Row):
    def __init__(
        self,
        initial: Path,
        on_change: Callable[[Path], None] | None = None,
    ) -> None:
        super().__init__()
        self.value: Path = initial
        self._on_change = on_change
        self._picker = ft.FilePicker()

        self._field = ft.TextField(
            label=t("destination"),
            value=str(initial),
            read_only=True,
            expand=True,
            prefix_icon=ft.Icons.FOLDER,
        )
        self._button = ft.OutlinedButton(
            t("choose_folder"), icon=ft.Icons.FOLDER_OPEN, on_click=self._pick
        )
        self.controls = [self._field, self._button]
        self.spacing = 10

    def did_mount(self) -> None:
        if self._picker not in self.page.services:
            self.page.services.append(self._picker)

    def set_value(self, path: Path) -> None:
        self.value = path
        self._field.value = str(path)

    async def _pick(self, e: ft.Event) -> None:
        selected = await self._picker.get_directory_path(
            dialog_title=t("choose_folder"), initial_directory=str(self.value)
        )
        if selected:
            self.value = Path(selected)
            self._field.value = selected
            if self._on_change:
                self._on_change(self.value)
            self.update()
