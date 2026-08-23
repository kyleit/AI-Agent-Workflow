"""CLI delivery — every command emits valid JSON with correct exit codes."""

import io
import json
from contextlib import redirect_stdout

from devteam.interface.cli.main import main


def _run(argv, root):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--root", root, *argv])
    return code, json.loads(buf.getvalue().strip())


def test_init_apply_then_send_poll(tmp_path):
    for d in ("src", "app"):
        (tmp_path / d).mkdir()
    root = str(tmp_path)
    code, out = _run(["init", "--apply"], root)
    assert code == 0 and out["ok"] is True

    code, out = _run(["mailbox", "send", "--to", "app", "--type", "task", "--json", '{"title":"x"}'], root)
    assert code == 0 and out["sent"]["to"] == "app"

    code, out = _run(["mailbox", "poll", "app"], root)
    assert code == 0 and len(out["messages"]) == 1

    code, out = _run(["board"], root)
    assert code == 0 and "DevTeam Board" in out["board"]


def test_unknown_seat_exit_2(tmp_path):
    (tmp_path / "src").mkdir()
    root = str(tmp_path)
    _run(["init", "--apply"], root)
    code, out = _run(["mailbox", "send", "--to", "ghost", "--type", "task", "--json", "{}"], root)
    assert code == 2 and out["ok"] is False and out["error"]["code"] == "UNKNOWN_SEAT"


def test_bad_json_payload_exit_2(tmp_path):
    (tmp_path / "src").mkdir()
    root = str(tmp_path)
    _run(["init", "--apply"], root)
    code, out = _run(["mailbox", "send", "--to", "src", "--type", "task", "--json", "{not json}"], root)
    assert code == 2 and out["error"]["code"] == "SCHEMA_INVALID"


def test_enter_leave_resume(tmp_path):
    (tmp_path / "src").mkdir()
    root = str(tmp_path)
    _run(["init", "--apply"], root)
    code, out = _run(["seat", "leave", "src", "--field", "next_step_now=pick up here"], root)
    assert code == 0
    code, out = _run(["seat", "enter", "src"], root)
    assert code == 0 and out["result"]["next_step_now"] == "pick up here"
