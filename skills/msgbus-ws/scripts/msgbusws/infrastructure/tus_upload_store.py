"""tus 1.0.0 resumable upload sessions: partial bytes + JSON metadata on disk."""
from __future__ import annotations

import json
import os
import secrets
import threading
from pathlib import Path

from ..domain.models import UploadSession
from ..domain.ports import UploadSessionStore


class TusUploadStore(UploadSessionStore):
    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _meta_path(self, upload_id: str) -> Path:
        return self._root / f"{upload_id}.json"

    def partial_path(self, upload_id: str) -> Path:
        return self._root / f"{upload_id}.part"

    def _write_meta(self, session: UploadSession) -> None:
        tmp = self._meta_path(session.upload_id).with_suffix(".json.tmp")
        tmp.write_text(json.dumps(session.to_dict(), ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self._meta_path(session.upload_id))

    def create(self, name: str, sender: str, to: str | None, length: int) -> UploadSession:
        upload_id = secrets.token_hex(16)
        session = UploadSession(upload_id=upload_id, name=name, sender=sender, to=to, length=length, offset=0)
        with self._lock:
            self.partial_path(upload_id).touch()
            self._write_meta(session)
        return session

    def get(self, upload_id: str) -> UploadSession | None:
        meta = self._meta_path(upload_id)
        if not meta.is_file():
            return None
        try:
            return UploadSession.from_dict(json.loads(meta.read_text(encoding="utf-8")))
        except (ValueError, KeyError):
            return None

    def write_chunk(self, upload_id: str, offset: int, data: bytes) -> int:
        with self._lock:
            session = self.get(upload_id)
            if session is None:
                raise KeyError(upload_id)
            if offset != session.offset:
                raise ValueError(f"offset mismatch: expected {session.offset}, got {offset}")
            with self.partial_path(upload_id).open("r+b") as f:
                f.seek(offset)
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            session.offset = offset + len(data)
            self._write_meta(session)
            return session.offset

    def discard(self, upload_id: str) -> None:
        with self._lock:
            for path in (self._meta_path(upload_id), self.partial_path(upload_id)):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
