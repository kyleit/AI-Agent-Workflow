import pytest

from devteam.application.acquire_lock import AcquireLockUseCase
from devteam.application.list_locks import ListLocksUseCase
from devteam.application.release_lock import ReleaseLockUseCase
from devteam.domain.errors import DevTeamError, ErrorCode
from devteam.infrastructure.paths import PathResolver
from devteam.infrastructure.repositories.lock_repo import FileLockRepository
from devteam.infrastructure.repositories.roster_repo import FileRosterRepository


class FakeClock:
    def __init__(self, iso):
        self.iso = iso

    def now_iso(self):
        return self.iso


def _wire(root, clock):
    paths = PathResolver(root)
    roster = FileRosterRepository(paths)
    locks = FileLockRepository(paths)
    return (
        AcquireLockUseCase(roster, locks, clock),
        ReleaseLockUseCase(locks),
        ListLocksUseCase(locks, clock),
    )


def test_acquire_then_conflict(team, root):
    clock = FakeClock("2026-01-01T12:00:00")
    acquire, _release, _list = _wire(root, clock)
    res = acquire.execute("shared/x.py", "src", note="editing")
    assert res["action"] == "GRANT"
    with pytest.raises(DevTeamError) as e:
        acquire.execute("shared/x.py", "app")
    assert e.value.code == ErrorCode.LOCK_CONFLICT
    assert e.value.details["holder"] == "src"


def test_release_non_holder_raises(team, root):
    clock = FakeClock("2026-01-01T12:00:00")
    acquire, release, _list = _wire(root, clock)
    acquire.execute("shared/x.py", "src")
    with pytest.raises(DevTeamError) as e:
        release.execute("shared/x.py", "app")
    assert e.value.code == ErrorCode.LOCK_NOT_HELD


def test_ttl_expiry_allows_takeover(team, root):
    early = FakeClock("2026-01-01T12:00:00")
    acquire_e, _r, _l = _wire(root, early)
    acquire_e.execute("shared/x.py", "src", ttl_seconds=60)
    # 2 minutes later, a different seat can take the expired lock
    late = FakeClock("2026-01-01T12:02:00")
    acquire_l, _r2, list_l = _wire(root, late)
    res = acquire_l.execute("shared/x.py", "app")
    assert res["action"] == "GRANT"
    assert res["lock"]["holder"] == "app"
    chk = list_l.check("shared/x.py")
    assert chk["held"] is True and chk["lock"]["holder"] == "app"


def test_acquire_unknown_seat(team, root):
    clock = FakeClock("2026-01-01T12:00:00")
    acquire, _r, _l = _wire(root, clock)
    with pytest.raises(DevTeamError) as e:
        acquire.execute("shared/x.py", "ghost")
    assert e.value.code == ErrorCode.UNKNOWN_SEAT
