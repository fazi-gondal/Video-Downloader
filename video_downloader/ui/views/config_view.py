"""Download configuration screen (mode, format, quality, destination).

Layout: fixed header + scrollable body + fixed bottom action bar with a
live summary of the chosen options.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from video_downloader.config.constants import (
    ANALYSIS_TIMEOUT_SECONDS,
    AUDIO_FORMATS,
    AUDIO_QUALITY_PRESETS,
    FPS_PRESETS,
    RESOLUTION_PRESETS,
    VIDEO_CONTAINERS,
)
from video_downloader.core.errors import AppError
from video_downloader.models.download import DownloadMode, DownloadRequest
from video_downloader.models.media import FormatInfo, MediaInfo, PlaylistInfo
from video_downloader.services.ytdlp_service import formats_for_display
from video_downloader.ui import theme
from video_downloader.ui.app import AppContext
from video_downloader.ui.components.buttons import primary_button
from video_downloader.ui.components.chip_group import ChipGroup
from video_downloader.ui.components.folder_picker import FolderPicker
from video_downloader.ui.components.format_table import FormatTable
from video_downloader.ui.components.option_cards import ModeSelector
from video_downloader.ui.components.status_pill import PILL_CORAL, StatusPill
from video_downloader.ui.texts import t
from video_downloader.ui.utils import safe_update

_CUSTOM_QUALITY = "Custom"


def _section_title(text: str) -> ft.Text:
    return ft.Text(text, style=theme.headline_md())


def _summary_chip(text: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(
            text, size=12, weight=ft.FontWeight.W_600, color=ft.Colors.ON_SURFACE
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=ft.BorderRadius.all(6),
        padding=ft.Padding.symmetric(vertical=4, horizontal=10),
    )


class ConfigView(ft.Column):
    def __init__(
        self,
        ctx: AppContext,
        on_started: Callable[[], None],
        on_back: Callable[[], None],
    ) -> None:
        super().__init__()
        self.ctx = ctx
        self.on_started = on_started
        self.on_back = on_back
        self.expand = True
        self.spacing = 14

        media = ctx.current_media
        self._is_playlist = isinstance(media, PlaylistInfo)
        self._manual_video: FormatInfo | None = None
        self._manual_audio: FormatInfo | None = None

        # --- Header (fixed) ------------------------------------------------
        title = media.title if media else ""
        subtitle = (
            f"{len(ctx.selected_entries)} {t('selected_count')}"
            if self._is_playlist
            else title
        )
        header_items: list[ft.Control] = [
            ft.IconButton(
                ft.Icons.ARROW_BACK, on_click=lambda e: self.on_back()
            ),
            ft.Column(
                [
                    ft.Text(t("config_title"), style=theme.headline_lg()),
                    ft.Text(
                        subtitle,
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                ],
                spacing=2,
                expand=True,
            ),
        ]
        if media is not None and media.thumbnail_url:
            header_items.append(
                ft.Container(
                    content=ft.Image(
                        src=media.thumbnail_url, width=85, height=48,
                        fit=ft.BoxFit.COVER,
                    ),
                    border_radius=ft.BorderRadius.all(8),
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                )
            )
        header = ft.Row(header_items, spacing=8)

        ffmpeg_warning = ft.Container(
            visible=not ctx.ffmpeg.is_available,
            bgcolor=ft.Colors.ERROR_CONTAINER,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.4, ft.Colors.ERROR)),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
            padding=12,
            content=ft.Text(t("ffmpeg_missing"), color=ft.Colors.ERROR),
        )

        settings = ctx.settings

        # --- Mode ------------------------------------------------------------
        self._mode_selector = ModeSelector(on_change=self._on_mode_change)

        # --- Video options (bento: container | quality) ----------------------
        self._container_cg = ChipGroup(
            VIDEO_CONTAINERS,
            sublabels={"mp4": t("recommended")},
            on_change=lambda v: self._refresh_summary(),
        )
        self._resolution_cg = ChipGroup(
            list(RESOLUTION_PRESETS),
            columns=3,
            on_change=lambda v: self._refresh_summary(),
        )
        self._fps_cg = ChipGroup(list(FPS_PRESETS))
        self._video_options = ft.Row(
            [
                ft.Column(
                    [
                        _section_title(t("container_section")),
                        self._container_cg,
                        ft.Container(height=6),
                        _section_title(t("fps")),
                        self._fps_cg,
                    ],
                    spacing=10,
                    expand=5,
                ),
                ft.Column(
                    [
                        _section_title(t("quality_section")),
                        self._resolution_cg,
                    ],
                    spacing=10,
                    expand=7,
                ),
            ],
            spacing=24,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        # --- Audio options ----------------------------------------------------
        self._audio_format_cg = ChipGroup(
            AUDIO_FORMATS, on_change=lambda v: self._refresh_summary()
        )
        self._audio_quality_cg = ChipGroup(
            [*AUDIO_QUALITY_PRESETS, _CUSTOM_QUALITY],
            on_change=self._on_quality_change,
        )
        self._custom_bitrate = ft.TextField(
            label=t("custom_bitrate"), width=240, visible=False, value="192"
        )
        self._audio_options = ft.Column(
            [
                _section_title(t("audio_section")),
                ft.Text(
                    t("audio_format"),
                    size=12.5,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                self._audio_format_cg,
                ft.Text(
                    t("audio_quality"),
                    size=12.5,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                self._audio_quality_cg,
                self._custom_bitrate,
            ],
            spacing=10,
            visible=False,
        )

        # --- Audio Tracks Menu ---------------------------------------------
        self._audio_tracks_mode = ChipGroup(
            [
                t("audio_tracks_mode_default"),
                t("audio_tracks_mode_all"),
                t("audio_tracks_mode_custom"),
            ],
            on_change=self._on_audio_track_mode_change,
        )
        self._audio_track_cbs: list[ft.Checkbox] = []
        if isinstance(media, MediaInfo) and media.audio_tracks:
            for track in media.audio_tracks:
                # Store the language code as the selector key — it is stable
                # across yt-dlp sessions (unlike indexed format IDs like '251-0'
                # which vanish without a JS runtime).  Fall back to format_id
                # only for tracks that have no language (rare default-only videos).
                selector_key = track.get("language") or track["format_id"]
                cb = ft.Checkbox(label=track["label"], data=selector_key, value=False)
                self._audio_track_cbs.append(cb)

        self._audio_tracks_custom_container = ft.Column(
            [
                ft.Text(t("select_audio_hint"), size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(
                    content=ft.Column(
                        self._audio_track_cbs if self._audio_track_cbs else [
                            ft.Text("No audio tracks detected", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
                        ],
                        spacing=4,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=200,
                    padding=10,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                ),
            ],
            spacing=8,
            visible=False,
        )

        self._audio_tracks_section = ft.Column(
            [
                _section_title(t("audio_tracks_section")),
                self._audio_tracks_mode,
                self._audio_tracks_custom_container,
            ],
            spacing=10,
        )

        # --- Subtitles Menu ------------------------------------------------
        self._subtitles_mode = ChipGroup(
            [
                t("subtitles_mode_none"),
                t("subtitles_mode_all"),
                t("subtitles_mode_custom"),
            ],
            on_change=self._on_subtitles_mode_change,
        )
        # Select default subtitle mode based on settings
        if settings.write_subtitles:
            self._subtitles_mode.set_value(t("subtitles_mode_all"))
        else:
            self._subtitles_mode.set_value(t("subtitles_mode_none"))

        self._subtitle_cbs: list[ft.Checkbox] = []
        if isinstance(media, MediaInfo) and media.subtitles:
            for code, name in media.subtitles.items():
                cb = ft.Checkbox(label=f"{name} ({code})", data=code, value=False)
                self._subtitle_cbs.append(cb)

        self._custom_subtitles_field = ft.TextField(
            label=t("subtitles_custom_langs"),
            hint_text="e.g. en, es, ar",
            value="",
            width=280,
        )

        self._subtitles_custom_container = ft.Column(
            [
                ft.Text(t("select_subtitles_hint"), size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Container(
                    content=ft.Column(
                        self._subtitle_cbs if self._subtitle_cbs else [
                            ft.Text("No subtitles detected", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
                        ],
                        spacing=4,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    height=200,
                    padding=10,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=ft.BorderRadius.all(theme.RADIUS_CONTROL),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                ),
                self._custom_subtitles_field,
            ],
            spacing=8,
            visible=False,
        )

        self._subtitles_section = ft.Column(
            [
                _section_title(t("subtitles_section")),
                self._subtitles_mode,
                self._subtitles_custom_container,
            ],
            spacing=10,
        )

        # --- Manual format selection (single video only) ----------------------
        self._formats_holder = ft.Column(spacing=8)
        self._manual_section = ft.ExpansionTile(
            title=ft.Text(
                t("manual_selection"),
                size=15,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
            ),
            subtitle=ft.Text(
                t("explore_formats"), size=12, color=ft.Colors.ON_SURFACE_VARIANT
            ),
            controls=[
                ft.Container(content=self._formats_holder, padding=12)
            ],
            on_change=self._on_manual_expand,
            visible=not self._is_playlist,
        )
        self._manual_summary = ft.Row(spacing=8, visible=False)

        # --- Extras -------------------------------------------------------
        self._thumbnail_cb = ft.Checkbox(
            label=t("embed_thumbnail"), value=settings.embed_thumbnail
        )
        self._metadata_cb = ft.Checkbox(
            label=t("embed_metadata"), value=settings.embed_metadata
        )
        extras = ft.Column(
            [
                _section_title(t("extras_section")),
                ft.Row(
                    [
                        self._thumbnail_cb,
                        self._metadata_cb,
                    ],
                    spacing=16,
                    wrap=True,
                ),
            ],
            spacing=10,
        )

        # --- Destination ----------------------------------------------------
        self._folder = FolderPicker(
            settings.download_path, on_change=lambda p: self._refresh_summary()
        )
        destination = ft.Column(
            [_section_title(t("destination_section")), self._folder], spacing=10
        )

        # --- Bottom action bar (fixed) ---------------------------------------
        count = len(ctx.selected_entries) if self._is_playlist else 1
        label = f"{t('download')} ({count})" if count > 1 else t("download")
        self._download_button = primary_button(
            label, icon=ft.Icons.DOWNLOAD, on_click=self._on_download
        )
        self._summary_row = ft.Row(spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        bottom_bar = ft.Container(
            content=ft.Row(
                [
                    self._summary_row,
                    ft.Container(expand=True),
                    self._download_button,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=12, horizontal=16),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
        )

        # --- Assembly ---------------------------------------------------------
        body = ft.Column(
            [
                self._mode_selector,
                ft.Divider(),
                self._video_options,
                self._audio_options,
                ft.Divider(),
                self._audio_tracks_section,
                self._subtitles_section,
                ft.Divider(),
                self._manual_section,
                self._manual_summary,
                extras,
                destination,
            ],
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.controls = [header, ffmpeg_warning, body, bottom_bar]
        self._refresh_summary()

    # ------------------------------------------------------------------

    def _on_audio_track_mode_change(self, value: str) -> None:
        self._audio_tracks_custom_container.visible = (value == t("audio_tracks_mode_custom"))
        safe_update(self)

    def _on_subtitles_mode_change(self, value: str) -> None:
        self._subtitles_custom_container.visible = (value == t("subtitles_mode_custom"))
        safe_update(self)

    def _on_mode_change(self, mode: DownloadMode) -> None:
        self._video_options.visible = mode is not DownloadMode.AUDIO_ONLY
        self._audio_options.visible = mode is DownloadMode.AUDIO_ONLY
        self._audio_tracks_section.visible = mode is DownloadMode.VIDEO_AUDIO
        self._subtitles_section.visible = mode is not DownloadMode.AUDIO_ONLY
        self._refresh_summary()
        safe_update(self)

    def _on_quality_change(self, value: str) -> None:
        self._custom_bitrate.visible = value == _CUSTOM_QUALITY
        self._refresh_summary()
        safe_update(self)

    def _refresh_summary(self) -> None:
        """Rebuild the bottom-bar chips: format · quality → destination."""
        mode = self._mode_selector.value
        if mode is DownloadMode.AUDIO_ONLY:
            fmt = (self._audio_format_cg.value or "mp3").upper()
            quality = self._audio_quality_cg.value or ""
        else:
            fmt = (self._container_cg.value or "mp4").upper()
            quality = self._resolution_cg.value or ""
        self._summary_row.controls = [
            _summary_chip(fmt),
            _summary_chip(quality),
            ft.Icon(ft.Icons.ARROW_FORWARD, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text(
                str(self._folder.value),
                size=12.5,
                color=ft.Colors.ON_SURFACE_VARIANT,
                max_lines=1,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ]
        safe_update(self)

    async def _on_manual_expand(self, e: ft.Event) -> None:
        media = self.ctx.current_media
        if not isinstance(media, MediaInfo) or self._formats_holder.controls:
            return
        spinner = ft.ProgressRing(width=16, height=16, stroke_width=2)
        self._formats_holder.controls = [
            ft.Row(
                [
                    spinner,
                    ft.Text(t("loading_formats"), color=ft.Colors.ON_SURFACE_VARIANT),
                ],
                spacing=8,
            )
        ]
        self.update()
        try:
            if not media.formats:
                full = await asyncio.wait_for(
                    asyncio.to_thread(self.ctx.ytdlp.fetch_formats, media.webpage_url),
                    timeout=ANALYSIS_TIMEOUT_SECONDS,
                )
                media.formats = full.formats
            table = FormatTable(
                formats_for_display(media),
                selectable=True,
                on_selection=self._on_manual_selection,
            )
            self._formats_holder.controls = [table]
        except TimeoutError:
            self._formats_holder.controls = [
                ft.Text(t("error_analysis_timeout"), color=ft.Colors.ERROR)
            ]
        except AppError as err:
            self._formats_holder.controls = [
                ft.Text(t(err.user_message_key), color=ft.Colors.ERROR)
            ]
        self.update()

    def _on_manual_selection(
        self, video: FormatInfo | None, audio: FormatInfo | None
    ) -> None:
        self._manual_video = video
        self._manual_audio = audio
        pills: list[ft.Control] = []
        if video:
            pills.append(
                StatusPill(f"{t('video_stream')}: {video.format_id}", PILL_CORAL)
            )
        if audio:
            pills.append(
                StatusPill(f"{t('audio_stream')}: {audio.format_id}", PILL_CORAL)
            )
        self._manual_summary.controls = pills
        self._manual_summary.visible = bool(pills)
        self.update()

    # ------------------------------------------------------------------

    def _on_download(self, e: ft.Event) -> None:
        media = self.ctx.current_media
        if media is None:
            return

        requests = self._build_requests(media)
        for request in requests:
            self.ctx.download_manager.enqueue(request)
        self.on_started()

    def _build_requests(self, media: MediaInfo | PlaylistInfo) -> list[DownloadRequest]:
        mode = self._mode_selector.value
        output_dir = self._folder.value

        bitrate: int | None
        quality = self._audio_quality_cg.value or ""
        if quality == _CUSTOM_QUALITY:
            try:
                bitrate = max(8, min(512, int(self._custom_bitrate.value or "192")))
            except ValueError:
                bitrate = 192
        else:
            bitrate = AUDIO_QUALITY_PRESETS.get(quality)

        # Subtitles configuration
        sub_mode = self._subtitles_mode.value
        write_subs = False
        sub_langs: tuple[str, ...] = ()
        if sub_mode == t("subtitles_mode_all"):
            write_subs = True
            sub_langs = ("all",)
        elif sub_mode == t("subtitles_mode_custom"):
            selected_codes = [cb.data for cb in self._subtitle_cbs if cb.value]
            custom_codes = [
                c.strip()
                for c in (self._custom_subtitles_field.value or "").split(",")
                if c.strip()
            ]
            all_codes = list(dict.fromkeys(selected_codes + custom_codes))
            if all_codes:
                write_subs = True
                sub_langs = tuple(all_codes)
            else:
                write_subs = False

        # Audio tracks configuration
        audio_mode = self._audio_tracks_mode.value
        multi_audio = False
        selected_audio_ids: tuple[str, ...] = ()
        if audio_mode == t("audio_tracks_mode_all"):
            multi_audio = True
        elif audio_mode == t("audio_tracks_mode_custom"):
            selected_audio_ids = tuple(
                str(cb.data) for cb in self._audio_track_cbs if cb.value
            )

        def make(
            url: str,
            title: str,
            playlist_title: str | None = None,
            playlist_index: int | None = None,
            video_format_id: str | None = None,
            audio_format_id: str | None = None,
            thumbnail_url: str | None = None,
        ) -> DownloadRequest:
            single_audio_id = audio_format_id
            track_ids = selected_audio_ids
            if len(selected_audio_ids) == 1 and not audio_format_id:
                key = selected_audio_ids[0]
                # If the key looks like a raw format ID (digits / dashes), put
                # it in audio_format_id so yt-dlp uses it directly.
                # If it is a language code (e.g. "de", "zh-Hant"), keep it in
                # selected_audio_track_ids so format_builder converts it to the
                # stable ba[language=XX] filter.
                import re as _re
                if _re.match(r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$", key):
                    track_ids = selected_audio_ids   # language → keep in track_ids
                else:
                    single_audio_id = key            # raw format ID → legacy path
                    track_ids = ()


            return DownloadRequest(
                url=url,
                title=title,
                mode=mode,
                output_dir=output_dir,
                container=self._container_cg.value or "mp4",
                max_height=RESOLUTION_PRESETS.get(self._resolution_cg.value or ""),
                max_fps=FPS_PRESETS.get(self._fps_cg.value or ""),
                audio_format=self._audio_format_cg.value or "mp3",
                audio_bitrate_kbps=bitrate,
                write_subtitles=write_subs,
                subtitle_langs=sub_langs,
                multi_audio=multi_audio,
                selected_audio_track_ids=track_ids,
                embed_thumbnail=bool(self._thumbnail_cb.value),
                embed_metadata=bool(self._metadata_cb.value),
                playlist_title=playlist_title,
                playlist_index=playlist_index,
                video_format_id=video_format_id,
                audio_format_id=single_audio_id,
                thumbnail_url=thumbnail_url,
            )

        if isinstance(media, PlaylistInfo):
            entries = self.ctx.selected_entries or media.entries
            return [
                make(
                    url=entry.url,
                    title=entry.title,
                    playlist_title=media.title,
                    playlist_index=entry.index,
                )
                for entry in entries
            ]

        return [
            make(
                url=media.webpage_url,
                title=media.title,
                video_format_id=self._manual_video.format_id if self._manual_video else None,
                audio_format_id=self._manual_audio.format_id if self._manual_audio else None,
                thumbnail_url=media.thumbnail_url,
            )
        ]
