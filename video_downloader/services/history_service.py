"""Download history persisted in SQLite (stdlib sqlite3)."""

from __future__ import annotations

import logging
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import platformdirs

from video_downloader.config.constants import APP_AUTHOR, APP_NAME
from video_downloader.models.download import DownloadState, DownloadTask

logger = logging.getLogger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS downloads (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    mode TEXT NOT NULL,
    container TEXT,
    audio_format TEXT,
    output_dir TEXT NOT NULL,
    output_path TEXT,
    state TEXT NOT NULL,
    error TEXT,
    created_at TEXT NOT NULL,
    finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_downloads_created ON downloads(created_at DESC);
"""


@dataclass(slots=True)
class HistoryEntry:
    id: str
    url: str
    title: str
    mode: str
    container: str | None
    audio_format: str | None
    output_dir: str
    output_path: str | None
    state: str
    error: str | None
    created_at: str
    finished_at: str | None


class HistoryService:
    def __init__(self, db_file: Path | None = None) -> None:
        self._file = db_file or (
            Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR)) / "history.db"
        )
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._file, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------

    def record(self, task: DownloadTask) -> None:
        """Insert or update the history row for *task* (terminal states)."""
        request = task.request
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO downloads
                        (id, url, title, mode, container, audio_format, output_dir,
                         output_path, state, error, created_at, finished_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        output_path=excluded.output_path,
                        state=excluded.state,
                        error=excluded.error,
                        finished_at=excluded.finished_at
                    """,
                    (
                        task.id,
                        request.url,
                        request.title,
                        request.mode.value,
                        request.container,
                        request.audio_format,
                        str(request.output_dir),
                        str(task.output_path) if task.output_path else None,
                        task.state.value,
                        task.error,
                        task.created_at.isoformat(timespec="seconds"),
                        task.finished_at.isoformat(timespec="seconds")
                        if task.finished_at
                        else datetime.now().isoformat(timespec="seconds"),
                    ),
                )
        except sqlite3.Error as exc:
            logger.warning("Could not record history for %s: %s", task.id, exc)

    def list_entries(self, limit: int = 200) -> list[HistoryEntry]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT * FROM downloads ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
            return [HistoryEntry(**dict(row)) for row in rows]
        except sqlite3.Error as exc:
            logger.warning("Could not read history: %s", exc)
            return []

    def delete(self, entry_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM downloads WHERE id = ?", (entry_id,))

    def clear(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM downloads")


def is_completed(entry: HistoryEntry) -> bool:
    return entry.state == DownloadState.COMPLETED.value
