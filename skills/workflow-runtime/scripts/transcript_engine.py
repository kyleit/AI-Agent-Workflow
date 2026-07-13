# transcript_engine.py
# IncrementalTranscriptReader — reads JSONL files incrementally with SQLite cursor tracking
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from typing import List, Optional, Tuple


class TranscriptParseError(Exception):
    """Raised when a transcript line cannot be parsed (soft — usually just logged)."""


class IncrementalTranscriptReader:
    """
    Reads JSONL transcript files incrementally using byte-position tracking.

    Each file's read position is persisted in the `transcript_cursors` SQLite
    table (inside project_runtime.db). Subsequent reads only return new lines
    since the last call.

    Thread safety: Not thread-safe. Use one instance per thread/process.

    Windows note: If the file is locked by another process, up to 3 retries
    with exponential backoff (100ms, 200ms, 400ms) are attempted before
    returning an empty list.
    """

    MAX_RETRY = 3
    RETRY_DELAYS = (0.1, 0.2, 0.4)  # seconds

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None):
        """
        Args:
            db_conn: SQLite connection for cursor persistence.
                     If None, cursors are tracked only in-memory (no persistence).
        """
        self._db = db_conn
        self._memory_cursors: dict = {}  # fallback when no db_conn

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def read_new_lines(self, file_path: str) -> List[Tuple[dict, int]]:
        """
        Return only the new JSONL lines since the last call for this file.

        Args:
            file_path: Absolute path to a .jsonl file.

        Returns:
            List of (parsed JSON dict, start_byte_offset) tuples (new content only).
        """
        file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            return []

        current_hash = self._compute_hash(file_path)
        saved_pos, saved_hash = self._load_cursor(file_path)

        # If hash unchanged AND we have a saved position → file unmodified
        if saved_hash and saved_hash == current_hash and saved_pos > 0:
            return []

        # Attempt to open the file (retry on PermissionError for Windows locks)
        for attempt, delay in enumerate(self.RETRY_DELAYS):
            try:
                lines = self._stream_from(file_path, saved_pos)
                # Compute new byte position after read
                new_pos = self._get_file_size(file_path)
                new_hash = self._compute_hash(file_path)
                self._save_cursor(file_path, new_pos, new_hash)
                return lines
            except PermissionError:
                if attempt < self.MAX_RETRY - 1:
                    time.sleep(delay)
                else:
                    return []
            except Exception:
                return []

        return []

    def get_file_hash(self, file_path: str) -> str:
        """Return current MD5-based hash string for a file."""
        return self._compute_hash(os.path.abspath(file_path))

    def reset(self, file_path: str) -> None:
        """
        Force a full re-read of the file on the next call.
        Clears the saved cursor for this file.
        """
        file_path = os.path.abspath(file_path)
        self._memory_cursors.pop(file_path, None)
        if self._db is not None:
            try:
                self._db.execute(
                    "DELETE FROM transcript_cursors WHERE file_path = ?",
                    (file_path,),
                )
                self._db.commit()
            except sqlite3.Error:
                pass

    # ------------------------------------------------------------------ #
    #  Internal: streaming read                                            #
    # ------------------------------------------------------------------ #

    def _stream_from(self, file_path: str, byte_pos: int) -> List[Tuple[dict, int]]:
        """Read new JSON lines from byte_pos to end of file, tracking start byte offsets."""
        lines = []
        with open(file_path, "rb") as f:
            if byte_pos > 0:
                f.seek(byte_pos)
            while True:
                start_offset = f.tell()
                line_bytes = f.readline()
                if not line_bytes:
                    break
                line_str = line_bytes.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue
                try:
                    parsed = json.loads(line_str)
                    lines.append((parsed, start_offset))
                except json.JSONDecodeError:
                    # Skip malformed lines silently
                    pass
        return lines

    # ------------------------------------------------------------------ #
    #  Internal: cursor persistence                                         #
    # ------------------------------------------------------------------ #

    def _load_cursor(self, file_path: str) -> Tuple[int, str]:
        """
        Load saved byte position and hash for a file.

        Returns:
            (byte_pos, file_hash) — (0, '') if no cursor saved.
        """
        if self._db is not None:
            try:
                row = self._db.execute(
                    "SELECT byte_pos, file_hash FROM transcript_cursors WHERE file_path = ?",
                    (file_path,),
                ).fetchone()
                if row:
                    return int(row[0]), str(row[1])
            except sqlite3.Error:
                pass
        # Fallback to in-memory
        entry = self._memory_cursors.get(file_path)
        if entry:
            return entry["byte_pos"], entry["file_hash"]
        return 0, ""

    def _save_cursor(self, file_path: str, byte_pos: int, file_hash: str) -> None:
        """Persist byte position and hash for a file."""
        now = datetime.now(timezone.utc).isoformat()
        if self._db is not None:
            try:
                self._db.execute(
                    """
                    INSERT INTO transcript_cursors (file_path, byte_pos, file_hash, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET
                        byte_pos = excluded.byte_pos,
                        file_hash = excluded.file_hash,
                        updated_at = excluded.updated_at
                    """,
                    (file_path, byte_pos, file_hash, now),
                )
                self._db.commit()
                return
            except sqlite3.Error:
                pass
        # Fallback to in-memory
        self._memory_cursors[file_path] = {
            "byte_pos": byte_pos,
            "file_hash": file_hash,
            "updated_at": now,
        }

    # ------------------------------------------------------------------ #
    #  Internal: hashing                                                   #
    # ------------------------------------------------------------------ #

    def _compute_hash(self, file_path: str) -> str:
        """
        Compute a lightweight hash for change detection.
        Uses MD5 of (file_path + file_size + mtime_ns) — fast, no file read.
        """
        try:
            stat = os.stat(file_path)
            raw = f"{file_path}:{stat.st_size}:{stat.st_mtime_ns}"
            return hashlib.md5(raw.encode()).hexdigest()
        except OSError:
            return ""

    def _get_file_size(self, file_path: str) -> int:
        """Return current file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0


def ensure_transcript_cursors_table(conn: sqlite3.Connection) -> None:
    """
    Ensure the transcript_cursors table exists in the given SQLite connection.
    Safe to call multiple times (CREATE TABLE IF NOT EXISTS).
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transcript_cursors (
            file_path   TEXT PRIMARY KEY,
            byte_pos    INTEGER NOT NULL DEFAULT 0,
            file_hash   TEXT NOT NULL DEFAULT '',
            updated_at  TEXT NOT NULL
        )
    """)
    conn.commit()
