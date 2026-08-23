"""ListLocksUseCase — list active locks; check a single path's holder."""

from __future__ import annotations

import datetime

from ..domain.locks.policy import is_expired
from ..domain.locks.resource_path import normalize_resource
from ..domain.ports import Clock, LockRepository


class ListLocksUseCase:
    def __init__(self, locks: LockRepository, clock: Clock) -> None:
        self._locks = locks
        self._clock = clock

    def execute(self) -> list[dict]:
        now = datetime.datetime.fromisoformat(self._clock.now_iso())
        out = []
        for lock in self._locks.all():
            d = lock.to_dict()
            d["expired"] = is_expired(lock, now)
            out.append(d)
        return out

    def check(self, path: str) -> dict:
        rp = normalize_resource(path)
        lock = self._locks.get(rp)
        if lock is None:
            return {"path": rp, "held": False}
        now = datetime.datetime.fromisoformat(self._clock.now_iso())
        return {"path": rp, "held": not is_expired(lock, now), "lock": lock.to_dict()}
