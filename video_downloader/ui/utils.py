"""Small UI helpers shared by views and components."""

from __future__ import annotations

import flet as ft


def is_mounted(control: ft.BaseControl) -> bool:
    """True when the control is attached to a page.

    In Flet 0.85 `control.page` raises RuntimeError for detached controls,
    so a plain `is not None` check is not enough.
    """
    try:
        return control.page is not None
    except RuntimeError:
        return False


def safe_update(control: ft.BaseControl) -> None:
    """Update the control only when mounted (no-op for offscreen views)."""
    if is_mounted(control):
        control.update()


def run_task(control: ft.BaseControl, handler) -> None:
    """Schedule an async task on the page's event loop (if mounted)."""
    try:
        page = control.page
    except RuntimeError:
        return
    if isinstance(page, ft.Page):
        page.run_task(handler)
