import pytest

from devteam.domain.errors import DevTeamError, ErrorCode
from devteam.domain.seats.role import Role
from devteam.domain.seats.roster import Roster
from devteam.domain.seats.seat import Seat
from devteam.domain.seats.write_set import WriteSet
from devteam.infrastructure.paths import PathResolver
from devteam.infrastructure.repositories.roster_repo import FileRosterRepository


def _roster():
    seats = (
        Seat("leader", Role("leader"), "L", WriteSet((".agents/devteam",)), ("workflow-coordinator",), "h"),
        Seat("src", Role("dev"), "S", WriteSet(("src",)), ("python-development",), "h"),
    )
    return Roster(1, "proj", "ts", seats)


def test_save_then_load_roundtrip(tmp_path):
    repo = FileRosterRepository(PathResolver(str(tmp_path)))
    assert not repo.exists()
    rel = repo.save(_roster())
    assert not rel.startswith("/") and ".." not in rel
    assert repo.exists()
    loaded = repo.load()
    assert loaded.leader().slug == "leader"
    assert loaded.by_slug("src").write_set.dirs == ("src",)


def test_load_missing_raises(tmp_path):
    repo = FileRosterRepository(PathResolver(str(tmp_path)))
    with pytest.raises(DevTeamError) as e:
        repo.load()
    assert e.value.code == ErrorCode.NOT_INITIALIZED
