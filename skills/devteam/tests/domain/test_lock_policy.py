import datetime

import pytest

from devteam.domain.errors import DevTeamError, ErrorCode
from devteam.domain.locks.lock import Lock
from devteam.domain.locks.policy import CONFLICT, GRANT, REFRESH, STEAL, decide, is_expired
from devteam.domain.locks.resource_path import normalize_resource

T0 = datetime.datetime(2026, 1, 1, 12, 0, 0)


def _lock(holder, expires=""):
    return Lock(path="p", holder=holder, ts="t", expires_at=expires)


def test_grant_when_free():
    assert decide(None, "a", T0, force=False) == GRANT


def test_refresh_same_holder():
    assert decide(_lock("a"), "a", T0, force=False) == REFRESH


def test_conflict_other_holder():
    assert decide(_lock("a"), "b", T0, force=False) == CONFLICT


def test_steal_with_force():
    assert decide(_lock("a"), "b", T0, force=True) == STEAL


def test_expired_lock_is_grantable():
    past = (T0 - datetime.timedelta(seconds=10)).isoformat()
    assert decide(_lock("a", past), "b", T0, force=False) == GRANT


def test_is_expired():
    assert is_expired(_lock("a", (T0 - datetime.timedelta(seconds=1)).isoformat()), T0)
    assert not is_expired(_lock("a", (T0 + datetime.timedelta(seconds=1)).isoformat()), T0)
    assert not is_expired(_lock("a", ""), T0)


def test_normalize_resource_rejects_absolute():
    with pytest.raises(DevTeamError) as e:
        normalize_resource("/etc/passwd")
    assert e.value.code == ErrorCode.ABSOLUTE_PATH


def test_normalize_resource_rejects_escape():
    with pytest.raises(DevTeamError) as e:
        normalize_resource("../secrets")
    assert e.value.code == ErrorCode.ABSOLUTE_PATH


def test_normalize_resource_ok():
    assert normalize_resource("src\\a\\b.py") == "src/a/b.py"
