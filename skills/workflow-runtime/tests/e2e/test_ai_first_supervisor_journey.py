from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(__file__).parents[2]


@dataclass(frozen=True)
class ProcessEvidence:
    argv: tuple[str, ...]
    exit_code: int
    payload: dict[str, Any]
    stdout: str
    stderr: str


@dataclass(frozen=True)
class JourneyEvidence:
    processes: tuple[ProcessEvidence, ...]
    workflow_id: str
    memory_status: str


def run_real_cli(root: Path, *argv: str) -> ProcessEvidence:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(RUNTIME_ROOT), env.get("PYTHONPATH", "")]
    )
    env["AIWF_TESTING"] = "true"
    env["AIWF_TESTING_BYPASS_ENFORCER"] = "true"
    env["AIWF_JSON_OUTPUT"] = "1"
    process = subprocess.run(
        [sys.executable, "-m", "workflow_runtime", *argv],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    lines = [line for line in process.stdout.splitlines() if line.strip()]
    assert len(lines) == 1, process.stdout
    payload = json.loads(lines[0])
    assert isinstance(payload, dict)
    return ProcessEvidence(
        argv=tuple(argv),
        exit_code=process.returncode,
        payload=payload,
        stdout=process.stdout,
        stderr=process.stderr,
    )


def materialize_action(action: dict[str, Any]) -> tuple[str, ...]:
    skill = str(action.get("skill") or "")
    command = str(action.get("command") or "")
    assert skill and command
    return (
        "start",
        "--skill",
        skill,
        "--command",
        command,
        "--checkpoint",
        "1",
        "--autonomous",
    )


def follow_until_gate(root: Path, request: str) -> JourneyEvidence:
    processes: list[ProcessEvidence] = [
        run_real_cli(root, "workflow", "submit", "--prompt", request)
    ]
    while processes[-1].payload.get("next_action", {}).get("automatic"):
        action = processes[-1].payload["next_action"]
        processes.append(run_real_cli(root, *materialize_action(action)))
        assert len(processes) <= 8

    first_data = processes[0].payload["data"]
    return JourneyEvidence(
        processes=tuple(processes),
        workflow_id=str(first_data["workflow_id"]),
        memory_status=str(first_data["memory"]["status"]),
    )


def test_ai_first_request_follows_runtime_action_through_real_processes(tmp_path: Path) -> None:
    (tmp_path / "AI_RULES.md").write_text("# isolated AIWF fixture\n", encoding="utf-8")

    evidence = follow_until_gate(tmp_path, "làm một thay đổi mới")

    assert evidence.workflow_id == "FEAT-001"
    assert evidence.memory_status == "bootstrapped"
    assert len(evidence.processes) == 2
    assert all(process.exit_code == 0 for process in evidence.processes)
    assert all(process.stderr == "" for process in evidence.processes)
    assert all(process.payload["schema_version"] == "aiwf.command.v1" for process in evidence.processes)
    assert evidence.processes[0].payload["next_action"]["automatic"] is True
    assert evidence.processes[1].payload["next_action"]["automatic"] is False

    workflow = json.loads(
        (tmp_path / ".agents" / "state" / "workflow.json").read_text(encoding="utf-8")
    )
    assert workflow["active_workflow"] == evidence.workflow_id

