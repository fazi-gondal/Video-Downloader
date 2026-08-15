"""About screen: app identity, developer credit and project links."""

from __future__ import annotations

import flet as ft

from video_downloader.config.constants import (
    APP_LICENSE,
    APP_TITLE,
    APP_VERSION,
    DEVELOPER_GITHUB_URL,
    DEVELOPER_LINKEDIN_URL,
    DEVELOPER_NAME,
    DEVELOPER_WEBSITE_URL,
    LICENSE_URL,
    REPO_ISSUES_URL,
    REPO_URL,
)
from video_downloader.ui import theme
from video_downloader.ui.texts import t

_TECH_STACK = ["Flet", "yt-dlp", "FFmpeg"]


def _link_button(text: str, icon: ft.IconData, url: str) -> ft.OutlinedButton:
    return ft.OutlinedButton(text, icon=icon, url=url)


class AboutView(ft.Column):
    def __init__(self) -> None:
        super().__init__()
        self.expand = True
        self.spacing = 0
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        logo = ft.Container(
            content=ft.Icon(ft.Icons.DOWNLOAD, size=40, color=ft.Colors.ON_PRIMARY),
            width=84,
            height=84,
            alignment=ft.Alignment.CENTER,
            bgcolor=ft.Colors.PRIMARY,
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD + 4),
        )
        version_pill = ft.Container(
            content=ft.Text(
                f"v{APP_VERSION} · {t('brand_subtitle')}",
                size=12.5,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
            padding=ft.Padding.symmetric(vertical=5, horizontal=14),
        )

        links: list[ft.Control] = [
            _link_button(t("link_github"), ft.Icons.CODE, DEVELOPER_GITHUB_URL),
        ]
        if DEVELOPER_LINKEDIN_URL:
            links.append(
                _link_button(
                    t("link_linkedin"),
                    ft.Icons.BUSINESS_CENTER_OUTLINED,
                    DEVELOPER_LINKEDIN_URL,
                )
            )
        if DEVELOPER_WEBSITE_URL:
            links.append(
                _link_button(
                    t("link_website"), ft.Icons.LANGUAGE, DEVELOPER_WEBSITE_URL
                )
            )
        links.append(
            _link_button(t("link_repo"), ft.Icons.FOLDER_SPECIAL_OUTLINED, REPO_URL)
        )
        links.append(
            _link_button(
                t("link_issues"), ft.Icons.BUG_REPORT_OUTLINED, REPO_ISSUES_URL
            )
        )

        tech_chips = ft.Row(
            [
                ft.Container(
                    content=ft.Text(
                        name, size=12.5, color=ft.Colors.ON_SURFACE_VARIANT
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
                    border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                    border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
                    padding=ft.Padding.symmetric(vertical=4, horizontal=14),
                )
                for name in _TECH_STACK
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        card = ft.Container(
            content=ft.Column(
                [
                    logo,
                    ft.Text(APP_TITLE, style=theme.headline_xl()),
                    version_pill,
                    ft.Container(
                        content=ft.Text(
                            t("about_description"),
                            size=14,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        width=460,
                        padding=ft.Padding.symmetric(vertical=6, horizontal=0),
                    ),
                    ft.Divider(),
                    ft.Text(
                        f"{t('developed_by')} {DEVELOPER_NAME}",
                        size=14,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Row(
                        links,
                        spacing=8,
                        wrap=True,
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=6),
                    ft.Text(
                        t("about_tech_label").upper(),
                        style=theme.label_md(ft.Colors.ON_SURFACE_VARIANT),
                    ),
                    tech_chips,
                    ft.Container(
                        content=ft.Text(
                            f"© 2026 {DEVELOPER_NAME} · {t('about_license')} "
                            f"{APP_LICENSE}",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        url=LICENSE_URL,
                        tooltip=t("about_license_tooltip"),
                        padding=ft.Padding.symmetric(vertical=4, horizontal=10),
                        border_radius=ft.BorderRadius.all(theme.RADIUS_PILL),
                        ink=True,
                    ),
                ],
                spacing=14,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding.symmetric(vertical=36, horizontal=40),
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=ft.BorderRadius.all(theme.RADIUS_CARD),
            width=620,
        )

        self.controls = [
            ft.Container(expand=1),
            ft.Column(
                [card],
                scroll=ft.ScrollMode.AUTO,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            ft.Container(expand=2),
        ]
