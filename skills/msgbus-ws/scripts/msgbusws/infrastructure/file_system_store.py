"""Filesystem-backed file store (basename-safe, atomic commit, Range-friendly)."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ..domain.models import FileMeta
from ..domain.ports import FileStore


class FileSystemStore(FileStore):
    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe(name: str) -> str:
        return os.path.basename(name)

    def _meta(self, path: Path) -> FileMeta:
        st = path.stat()
        return FileMeta(path.name, st.st_size, datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat())

    def commit_file(self, name: str, src: Path) -> FileMeta:
        dst = self._root / self._safe(name)
        shutil.move(str(src), str(dst))
        return self._meta(dst)

    def resolve(self, name: str) -> Path | None:
        path = self._root / self._safe(name)
        return path if path.is_file() else None

    def list(self) -> list[FileMeta]:
        out: list[FileMeta] = []
        for path in sorted(self._root.iterdir()):
            if path.is_file():
                out.append(self._meta(path))
        return out
