"""Tests for toast and SnackBar notifications."""

from unittest.mock import MagicMock

import flet as ft

from video_downloader.ui.components.toast import show_snack_bar, show_toast


def test_show_toast_uses_show_dialog():
    mock_page = MagicMock()
    show_toast(mock_page, "Download complete")

    mock_page.show_dialog.assert_called_once()
    snack = mock_page.show_dialog.call_args[0][0]
    assert isinstance(snack, ft.SnackBar)
    assert snack.behavior == ft.SnackBarBehavior.FLOATING
    assert snack.duration == 3500


def test_show_snack_bar_alias():
    mock_page = MagicMock()
    show_snack_bar(mock_page, "Test snack", icon=ft.Icons.ERROR_OUTLINE, color=ft.Colors.ERROR)

    mock_page.show_dialog.assert_called_once()
    snack = mock_page.show_dialog.call_args[0][0]
    assert isinstance(snack, ft.SnackBar)


def test_show_toast_fallback_when_show_dialog_fails():
    mock_page = MagicMock()
    mock_page.show_dialog.side_effect = RuntimeError("Dialog failure")
    mock_page.overlay = []

    # Should not raise, falls back to overlay card
    show_toast(mock_page, "Fallback message")
    mock_page.run_task.assert_called_once()
