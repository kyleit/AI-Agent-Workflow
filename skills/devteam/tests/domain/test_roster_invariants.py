import pytest

from devteam.domain.errors import DevTeamError, ErrorCode
from devteam.domain.seats.role import Role
from devteam.domain.seats.roster import Roster
from devteam.domain.seats.seat import Seat
from devteam.domain.seats.write_set import WriteSet


def _seat(slug, role, dirs):
    return Seat(slug, Role(role), slug, WriteSet(tuple(dirs)), (), "")


def test_requires_exactly_one_leader():
    r = Roster(1, "p", "t", (_seat("a", "dev", ["a"]), _seat("b", "dev", ["b"])))
    with pytest.raises(DevTeamError) as e:
        r.validate()
    assert e.value.code == ErrorCode.DUPLICATE_LEADER


def test_rejects_two_leaders():
    r = Roster(1, "p", "t", (_seat("a", "leader", ["a"]), _seat("b", "leader", ["b"])))
    with pytest.raises(DevTeamError) as e:
        r.validate()
    assert e.value.code == ErrorCode.DUPLICATE_LEADER


def test_rejects_duplicate_slug():
    r = Roster(1, "p", "t", (_seat("a", "leader", ["x"]), _seat("a", "dev", ["y"])))
    with pytest.raises(DevTeamError) as e:
        r.validate()
    assert e.value.code == ErrorCode.SCHEMA_INVALID


def test_rejects_bad_slug():
    r = Roster(1, "p", "t", (_seat("Leader!", "leader", ["x"]),))
    with pytest.raises(DevTeamError) as e:
        r.validate()
    assert e.value.code == ErrorCode.SCHEMA_INVALID


def test_rejects_overlapping_write_sets():
    r = Roster(1, "p", "t", (_seat("l", "leader", ["ctl"]), _seat("d", "dev", ["src"]), _seat("e", "dev", ["src/inner"])))
    with pytest.raises(DevTeamError) as e:
        r.validate()
    assert e.value.code == ErrorCode.WRITESET_OVERLAP


def test_valid_roster_passes_and_finds_leader():
    r = Roster(1, "p", "t", (_seat("l", "leader", ["ctl"]), _seat("d", "dev", ["src"]))).validate()
    assert r.leader().slug == "l"
    assert r.by_slug("d").slug == "d"
