"""Card showing analyzed media metadata (thumbnail, title, author, duration)."""

from __future__ import annotations

import flet as ft

from video_downloader.models.media import MediaInfo, PlaylistInfo
from video_downloader.ui import theme
from video_downloader.ui.texts import t
from video_downloader.utils.formatting import human_duration


def _meta_pill(icon: ft.IconData, text: str) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(text, size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            spacing=6,
            tight=True,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
        padding=ft.Padding.symmetric(vertical=4, horizontal=12),
    )


class MediaCard(ft.Container):
    def __init__(self, media: MediaInfo | PlaylistInfo) -> None:
        super().__init__(
            padding=16,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
        )
        is_playlist = isinstance(media, PlaylistInfo)

        thumbnail: ft.Control
        if media.thumbnail_url:
            thumbnail = ft.Container(
                content=ft.Image(
                    src=media.thumbnail_url,
                    width=200,
                    height=112,
                    fit=ft.BoxFit.COVER,
                ),
                border_radius=ft.BorderRadius.all(10),
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            )
        else:
            thumbnail = ft.Container(
                width=200,
                height=112,
                border_radius=ft.BorderRadius.all(10),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                content=ft.Icon(
                    ft.Icons.PLAYLIST_PLAY if is_playlist else ft.Icons.MOVIE,
                    size=44,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                alignment=ft.Alignment.CENTER,
            )

        pills: list[ft.Control] = []
        if isinstance(media, PlaylistInfo):
            pills.append(
                _meta_pill(
                    ft.Icons.PLAYLIST_PLAY, f"{media.entry_count} {t('videos_found')}"
                )
            )
        else:
            pills.append(_meta_pill(ft.Icons.SCHEDULE, human_duration(media.duration)))
        if media.uploader:
            pills.insert(0, _meta_pill(ft.Icons.PERSON_OUTLINE, media.uploader))

        details: list[ft.Control] = [
            ft.Text(
                media.title,
                style=theme.headline_md(),
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
            ft.Row(pills, spacing=8, wrap=True),
        ]

        self.content = ft.Row(
            [
                thumbnail,
                ft.Column(
                    details,
                    spacing=10,
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=16,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
