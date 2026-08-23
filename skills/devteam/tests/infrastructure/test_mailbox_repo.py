from devteam.domain.mailbox.envelope import Envelope
from devteam.infrastructure.paths import PathResolver
from devteam.infrastructure.repositories.mailbox_repo import JsonlMailboxRepository


def _repo(root):
    return JsonlMailboxRepository(PathResolver(root))


def _env(i):
    return Envelope(id=f"id{i}", frm="seat-l", to="seat-x", ts="t", type="msg", body=str(i))


def test_append_read_cursor(tmp_path):
    r = _repo(str(tmp_path))
    r.ensure_inbox("x")
    r.append("x", _env(0))
    r.append("x", _env(1))
    assert r.cursor("x") == 0
    got = r.read_from("x", 0)
    assert [e.body for e in got] == ["0", "1"]
    r.set_cursor("x", 2)
    assert r.cursor("x") == 2
    assert r.read_from("x", 2) == []


def test_read_missing_inbox_is_empty(tmp_path):
    r = _repo(str(tmp_path))
    assert r.read_from("nobody", 0) == []
    assert r.cursor("nobody") == 0
