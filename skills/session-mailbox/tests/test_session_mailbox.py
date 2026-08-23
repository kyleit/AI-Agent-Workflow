import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "session_mailbox.py"


def run_mailbox(*args: str, bus_root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--bus-root", str(bus_root), *args],
        text=True,
        capture_output=True,
        check=False,
    )


def test_send_escapes_backslashes_as_valid_json(tmp_path: Path) -> None:
    bus_root = tmp_path / "bus"
    message = r'bad escape sample: folder\name and literal \u1former'

    result = run_mailbox(
        "send",
        "--from",
        "sender",
        "--to",
        "receiver",
        "--message",
        message,
        bus_root=bus_root,
    )

    assert result.returncode == 0, result.stderr
    inbox = bus_root / "sessions" / "receiver.inbox.jsonl"
    raw = inbox.read_text(encoding="utf-8").strip()
    parsed = json.loads(raw)
    assert parsed["content"] == message


def test_validate_detects_and_repair_quarantines_bad_lines(tmp_path: Path) -> None:
    bus_root = tmp_path / "bus"
    inbox = bus_root / "sessions" / "receiver.inbox.jsonl"
    inbox.parent.mkdir(parents=True)
    inbox.write_text('{"ok":true}\n{"bad":"\\q"}\n', encoding="utf-8")

    invalid = run_mailbox("validate", "--file", str(inbox), bus_root=bus_root)
    assert invalid.returncode == 1
    assert '"bad": 1' in invalid.stdout

    repaired = run_mailbox("repair", "--file", str(inbox), bus_root=bus_root)
    assert repaired.returncode == 0
    assert '"status": "repaired"' in repaired.stdout
    assert inbox.read_text(encoding="utf-8").strip() == '{"ok":true}'
    assert inbox.with_suffix(".jsonl.bad").exists()


def test_append_rejects_invalid_json_without_touching_mailbox(tmp_path: Path) -> None:
    bus_root = tmp_path / "bus"
    inbox = bus_root / "sessions" / "receiver.inbox.jsonl"

    result = run_mailbox(
        "append",
        "--file",
        str(inbox),
        "--record-json",
        '{"bad":"\\q"}',
        bus_root=bus_root,
    )

    assert result.returncode == 1
    assert "invalid_json" in result.stderr
    assert not inbox.exists()
