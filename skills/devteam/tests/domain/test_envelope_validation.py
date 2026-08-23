import pytest

from devteam.domain.errors import DevTeamError, ErrorCode
from devteam.domain.mailbox.envelope import Envelope


def _base(**kw):
    d = {"from": "seat-a", "to": "seat-b", "type": "task"}
    d.update(kw)
    return d


def test_valid_envelope_roundtrips():
    env = Envelope.from_dict(_base(title="hi", state="queued"))
    d = env.to_dict()
    assert d["from"] == "seat-a" and d["type"] == "task" and d["state"] == "queued"


def test_rejects_bad_type():
    with pytest.raises(DevTeamError) as e:
        Envelope.from_dict(_base(type="nope"))
    assert e.value.code == ErrorCode.SCHEMA_INVALID


def test_rejects_bad_state():
    with pytest.raises(DevTeamError) as e:
        Envelope.from_dict(_base(state="weird"))
    assert e.value.code == ErrorCode.SCHEMA_INVALID


def test_rejects_unknown_keys():
    with pytest.raises(DevTeamError) as e:
        Envelope.from_dict(_base(hacker="x"))
    assert e.value.code == ErrorCode.SCHEMA_INVALID


def test_rejects_absolute_evidence_path():
    with pytest.raises(DevTeamError) as e:
        Envelope.from_dict(_base(evidence="/etc/passwd"))
    assert e.value.code == ErrorCode.ABSOLUTE_PATH


def test_rejects_escaping_evidence_path():
    with pytest.raises(DevTeamError) as e:
        Envelope.from_dict(_base(evidence="../../secrets"))
    assert e.value.code == ErrorCode.ABSOLUTE_PATH


def test_missing_required_keys():
    with pytest.raises(DevTeamError):
        Envelope.from_dict({"from": "a", "type": "task"})
