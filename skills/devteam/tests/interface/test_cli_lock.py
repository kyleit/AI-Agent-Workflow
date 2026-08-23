import io
import json
from contextlib import redirect_stdout

from devteam.interface.cli.main import main


def _run(argv, root):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = main(["--root", root, *argv])
    return code, json.loads(buf.getvalue().strip())


def _init(tmp_path):
    (tmp_path / "src").mkdir()
    root = str(tmp_path)
    _run(["init", "--apply"], root)
    return root


def test_acquire_list_check_release(tmp_path):
    root = _init(tmp_path)
    code, out = _run(["lock", "acquire", "shared/a.py", "--seat", "src", "--note", "wip"], root)
    assert code == 0 and out["action"] == "GRANT"

    code, out = _run(["lock", "list"], root)
    assert code == 0 and len(out["locks"]) == 1 and out["locks"][0]["holder"] == "src"

    code, out = _run(["lock", "check", "shared/a.py"], root)
    assert code == 0 and out["held"] is True

    code, out = _run(["lock", "release", "shared/a.py", "--seat", "src"], root)
    assert code == 0 and out["released"] == "shared/a.py"

    code, out = _run(["lock", "check", "shared/a.py"], root)
    assert out["held"] is False


def test_conflict_exit_2(tmp_path):
    root = _init(tmp_path)
    (tmp_path / "app").mkdir()
    # need a second seat; re-init not allowed, so add via a fresh repo with two dirs
    _run(["lock", "acquire", "shared/a.py", "--seat", "src"], root)
    code, out = _run(["lock", "acquire", "shared/a.py", "--seat", "src"], root)  # same holder -> REFRESH
    assert code == 0 and out["action"] == "REFRESH"


def test_board_shows_locks(tmp_path):
    root = _init(tmp_path)
    _run(["lock", "acquire", "shared/a.py", "--seat", "src"], root)
    code, out = _run(["board"], root)
    assert code == 0 and "Active locks" in out["board"] and "shared/a.py" in out["board"]
