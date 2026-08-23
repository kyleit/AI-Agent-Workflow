"""AcquireLockUseCase — take an exclusive cross-seat lock on a resource path."""

from __future__ import annotations

import datetime

from ..domain.errors import DevTeamError, ErrorCode
from ..domain.locks.policy import CONFLICT
from ..domain.locks.resource_path import normalize_resource
from ..domain.ports import Clock, LockRepository, RosterRepository


class AcquireLockUseCase:
    def __init__(self, roster: RosterRepository, locks: LockRepository, clock: Clock) -> None:
        self._roster = roster
        self._locks = locks
        self._clock = clock

    def execute(
        self, path: str, seat: str, note: str = "", ttl_seconds: int = 0, force: bool = False
    ) -> dict:
        rp = normalize_resource(path)
        self._roster.load().by_slug(seat)  # UNKNOWN_SEAT if bad
        now_iso = self._clock.now_iso()
        expires_at = ""
        if ttl_seconds and ttl_seconds > 0:
            expires_at = (
                datetime.datetime.fromisoformat(now_iso)
                + datetime.timedelta(seconds=ttl_seconds)
            ).isoformat()
        action, lock = self._locks.acquire(rp, seat, note, expires_at, force, now_iso)
        if action == CONFLICT:
            raise DevTeamError(
                ErrorCode.LOCK_CONFLICT,
                f"{rp} is held by {lock.holder if lock else 'another seat'}",
                {"holder": lock.holder if lock else "", "expires_at": lock.expires_at if lock else ""},
            )
        return {"action": action, "lock": lock.to_dict()}
