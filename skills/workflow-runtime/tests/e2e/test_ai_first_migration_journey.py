from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).parents[4]


def test_update_script_machine_contract_is_single_json_document() -> None:
    env = os.environ.copy()
    env["AIWF_JSON_OUTPUT"] = "1"
    process = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(ROOT / "update.ps1"), "--json"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert process.returncode == 0
    lines = [line for line in process.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, process.stdout
    payload = json.loads(lines[0])
    assert payload["schema"] == "aiwf.command.v1"
    assert payload["command"] == "update"
    assert payload["status"] == "skipped"
    assert payload["reason"] == "source_repository"
