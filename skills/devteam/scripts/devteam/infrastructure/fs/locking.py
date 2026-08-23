"""Cross-process advisory file lock (POSIX fcntl / Windows msvcrt).

O_APPEND is NOT reliably atomic across independent handles on win32, so every
inbox append is serialized by an exclusive lock on a sidecar ``<path>.lock``.
The lock is held by the open file description, so it also serializes threads
within a process. This is what guarantees zero lost/interleaved lines (AC3).
"""

from __future__ import annotations

import contextlib
import os
import time

try:  # POSIX
    import fcntl

    _HAVE_FCNTL = True
except ImportError:  # Windows
    import msvcrt

    _HAVE_FCNTL = False


@contextlib.contextmanager
def file_lock(lock_path: str, timeout: float = 15.0, poll: float = 0.005):
    os.makedirs(os.path.dirname(lock_path) or ".", exist_ok=True)
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        _acquire(fd, timeout, poll)
        try:
            yield
        finally:
            _release(fd)
    finally:
        os.close(fd)


def _acquire(fd: int, timeout: float, poll: float) -> None:
    deadline = time.monotonic() + timeout
    while True:
        try:
            if _HAVE_FCNTL:
                fcntl.flock(fd, fcntl.LOCK_EX)  # blocks until acquired
            else:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)  # non-blocking; raises if held
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(poll)


def _release(fd: int) -> None:
    try:
        if _HAVE_FCNTL:
            fcntl.flock(fd, fcntl.LOCK_UN)
        else:
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    except OSError:
        pass
