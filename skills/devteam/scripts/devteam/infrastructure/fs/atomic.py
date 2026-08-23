"""Atomic filesystem primitives.

``append_line`` performs a single ``os.write`` of one newline-terminated line
under ``O_APPEND``. For our small line sizes this is atomic on both POSIX and
win32, so concurrent senders never interleave or corrupt a line (no advisory
locks needed).

``atomic_write`` writes via a temp file + ``os.replace`` (atomic rename).
"""

from __future__ import annotations

import os
import tempfile

from .locking import file_lock


def append_line(path: str, line: str) -> None:
    """Append one newline-terminated line, serialized by a cross-process lock.

    The exclusive lock (see ``locking.file_lock``) guarantees no concurrent
    writer can interleave or lose a line — O_APPEND alone is not atomic across
    independent handles on win32.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload = line if line.endswith("\n") else line + "\n"
    data = payload.encode("utf-8")
    with file_lock(path + ".lock"):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)


def atomic_write(path: str, content: str) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
