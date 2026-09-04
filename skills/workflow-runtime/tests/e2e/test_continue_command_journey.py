from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _run_cli(tmp_path, *args: str) -> subprocess.CompletedProcess[str]:
    (tmp_path / ".agents").mkdir(exist_ok=True)
    (tmp_path / ".agents" / "AI_RULES.md").write_text("# test\n", encoding="utf-8")
    env = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[1].parent)
    env["PYTHONPATH"] = source_root + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "workflow_runtime", *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_continue_cli_active_workflow_is_machine_readable(tmp_path) -> None:
    state_dir = tmp_path / ".agents" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "workflow.json").write_text(
        json.dumps(
            {
                "active_workflow": "FIX-429",
                "active_phase": "implementation",
                "suggested_next_skill": "blueprint-to-implementation",
                "suggested_next_command": "implement",
            }
        ),
        encoding="utf-8",
    )

    result = _run_cli(tmp_path, "continue", "--json")

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["command"] == "continue"
    assert payload["status"] == "success"
    assert payload["data"]["workflow_id"] == "FIX-429"
    assert payload["next_action"]["automatic"] is True


def test_continue_cli_missing_state_is_explicit_hard_stop(tmp_path) -> None:
    result = _run_cli(tmp_path, "continue")

    assert result.returncode == 3
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["data"]["reason"] == "WORKFLOW_STATE_NOT_FOUND"
