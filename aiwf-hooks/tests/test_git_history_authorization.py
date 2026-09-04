from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


GATE = Path(__file__).resolve().parents[1] / "aiwf_gate.py"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=root, check=True, capture_output=True, text=True,
    )
    return result.stdout.strip()


def _check_files(root: Path, local_sha: str, remote_sha: str, file_path: str) -> subprocess.CompletedProcess[str]:
    payload = f"{local_sha}\t{remote_sha}\t{file_path}\n"
    return subprocess.run(
        [sys.executable, str(GATE), "check-files"],
        cwd=root,
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )


def test_pre_push_requires_exact_authorized_commit_receipt(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "aiwf@example.invalid")
    _git(tmp_path, "config", "user.name", "AIWF Test")
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents" / "AI_RULES.md").write_text("# test\n", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('one')\n", encoding="utf-8")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-qm", "initial")
    parent = _git(tmp_path, "rev-parse", "HEAD")
    (tmp_path / "app.py").write_text("print('two')\n", encoding="utf-8")
    _git(tmp_path, "add", "app.py")
    _git(tmp_path, "commit", "-qm", "change")
    local = _git(tmp_path, "rev-parse", "HEAD")

    blocked = _check_files(tmp_path, local, parent, "app.py")
    assert blocked.returncode == 1
    assert "Unauthorized source files" in blocked.stderr

    audit_dir = tmp_path / ".agents" / "state" / "audit"
    audit_dir.mkdir(parents=True)
    (audit_dir / "receipt.json").write_text(
        json.dumps({
            "work_item_id": "FIX-029_seamless_git_push_gate",
            "commit_sha": local,
            "authorized": True,
            "status": "AUTHORIZED",
        }),
        encoding="utf-8",
    )
    allowed = _check_files(tmp_path, local, parent, "app.py")
    assert allowed.returncode == 0, allowed.stderr

