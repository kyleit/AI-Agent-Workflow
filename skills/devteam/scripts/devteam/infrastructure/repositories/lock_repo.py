"""FileLockRepository — atomic cross-seat lock registry (.agents/devteam/locks.json).

Every mutation runs inside the cross-process ``file_lock`` on ``locks.json.lock``
so check-and-set is atomic across processes (same primitive as the mailbox).
"""

from __future__ import annotations

import datetime
import json
import os

from ...domain.locks.lock import Lock
from ...domain.locks.policy import CONFLICT, decide
from ..fs.atomic import atomic_write
from ..fs.locking import file_lock
from ..paths import PathResolver


class FileLockRepository:
    def __init__(self, paths: PathResolver) -> None:
        self._p = paths

    def _load(self) -> dict:
        path = self._p.locks_json()
        if not os.path.exists(path):
            return {}
        raw = open(path, encoding="utf-8-sig").read().strip()
        return json.loads(raw) if raw else {}

    def _save(self, reg: dict) -> None:
        atomic_write(self._p.locks_json(), json.dumps(reg, indent=2, ensure_ascii=False) + "\n")

    @staticmethod
    def _to_lock(path: str, entry: dict | None) -> Lock | None:
        if not entry:
            return None
        return Lock(
            path=path,
            holder=entry.get("holder", ""),
            ts=entry.get("ts", ""),
            note=entry.get("note", ""),
            expires_at=entry.get("expires_at", ""),
        )

    def all(self) -> list[Lock]:
        reg = self._load()
        return [self._to_lock(p, e) for p, e in reg.items() if e]

    def get(self, path: str) -> Lock | None:
        return self._to_lock(path, self._load().get(path))

    def acquire(
        self, path: str, holder: str, note: str, expires_at: str, force: bool, now_iso: str
    ) -> tuple[str, Lock | None]:
        with file_lock(self._p.locks_json() + ".lock"):
            reg = self._load()
            existing = self._to_lock(path, reg.get(path))
            now = datetime.datetime.fromisoformat(now_iso)
            action = decide(existing, holder, now, force)
            if action == CONFLICT:
                return CONFLICT, existing
            reg[path] = {"holder": holder, "ts": now_iso, "note": note, "expires_at": expires_at}
            self._save(reg)
            return action, Lock(path, holder, now_iso, note, expires_at)

    def release(self, path: str, holder: str, force: bool) -> bool:
        with file_lock(self._p.locks_json() + ".lock"):
            reg = self._load()
            entry = reg.get(path)
            if not entry:
                return False
            if entry.get("holder") != holder and not force:
                return False
            del reg[path]
            self._save(reg)
            return True
