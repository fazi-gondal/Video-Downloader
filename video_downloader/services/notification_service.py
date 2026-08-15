"""Desktop notifications (macOS via osascript; no-op elsewhere)."""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


class NotificationService:
    def notify(self, title: str, message: str) -> None:
        if sys.platform == "darwin":
            self._notify_macos(title, message)
        elif sys.platform.startswith("linux"):
            self._notify_linux(title, message)
        # Windows: no-op for now

    @staticmethod
    def _notify_macos(title: str, message: str) -> None:
        script = (
            f'display notification "{_escape(message)}" '
            f'with title "{_escape(title)}"'
        )
        try:
            subprocess.run(["osascript", "-e", script], check=False, timeout=5)
        except (OSError, subprocess.SubprocessError) as exc:
            logger.debug("Notification failed: %s", exc)

    @staticmethod
    def _notify_linux(title: str, message: str) -> None:
        try:
            subprocess.run(["notify-send", title, message], check=False, timeout=5)
        except (OSError, subprocess.SubprocessError) as exc:
            logger.debug("Notification failed: %s", exc)


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')
