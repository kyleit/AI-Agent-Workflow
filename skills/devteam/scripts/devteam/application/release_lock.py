"""ReleaseLockUseCase — release a lock held by the seat (or force)."""

from __future__ import annotations

from ..domain.errors import DevTeamError, ErrorCode
from ..domain.locks.resource_path import normalize_resource
from ..domain.ports import LockRepository


class ReleaseLockUseCase:
    def __init__(self, locks: LockRepository) -> None:
        self._locks = locks

    def execute(self, path: str, seat: str, force: bool = False) -> dict:
        rp = normalize_resource(path)
        released = self._locks.release(rp, seat, force)
        if not released:
            raise DevTeamError(
                ErrorCode.LOCK_NOT_HELD,
                f"{rp} is not held by {seat} (use --force to steal-release)",
            )
        return {"released": rp}
