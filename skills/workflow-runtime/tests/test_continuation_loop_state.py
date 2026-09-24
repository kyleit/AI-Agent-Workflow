"""Canonical contract test: continue_workflow reads the loop-controller state.

Pins the ONE true path for loop-state so downstream/E2E authors do not guess:
    .agents/state/loop/<workflow-id>.json   (schema aiwf.loop/1)
NOT .agents/runtime/loop-state.json (which no component writes).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from workflow_runtime.presentation.cli.commands._impl.workflow.continuation import (
    continue_workflow,
)

pytestmark = pytest.mark.unit


def _write_loop_state(root: Path, workflow_id: str, phase: str, stops: list[str]) -> None:
    loop_dir = root / ".agents" / "state" / "loop"
    loop_dir.mkdir(parents=True, exist_ok=True)
    (loop_dir / f"{workflow_id}.json").write_text(
        json.dumps({
            "schema": "aiwf.loop/1",
            "workflow_id": workflow_id,
            "current_phase": phase,
            "iteration": 1,
            "max_iterations": 8,
            "no_progress_count": 0,
            "no_progress_threshold": 3,
            "stop_conditions_met": stops,
        }),
        encoding="utf-8",
    )


def test_continue_reads_canonical_loop_state(tmp_path: Path) -> None:
    _write_loop_state(tmp_path, "FEAT-LOOP", "blueprint", [])
    result = continue_workflow(tmp_path)
    assert result.status == "success"
    assert result.data.get("state_source") == "loop"
    assert result.next_action is not None
    assert result.next_action.skill == "workflow-coordinator"


def test_continue_halted_loop_blocks_and_surfaces_stop(tmp_path: Path) -> None:
    _write_loop_state(tmp_path, "FEAT-HALT", "blueprint", ["NO_PROGRESS"])
    result = continue_workflow(tmp_path)
    assert result.status == "blocked"
    assert "LOOP_HALTED" in str(result.data.get("reason"))


def test_continue_missing_state_is_not_found(tmp_path: Path) -> None:
    result = continue_workflow(tmp_path)
    assert result.status == "blocked"
    assert result.data.get("reason") == "WORKFLOW_STATE_NOT_FOUND"


def test_runtime_loop_state_path_is_not_consulted(tmp_path: Path) -> None:
    # A file at the phantom .agents/runtime/loop-state.json MUST NOT satisfy
    # continuation; only the canonical .agents/state/loop/<id>.json does.
    runtime_dir = tmp_path / ".agents" / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "loop-state.json").write_text(
        json.dumps({"schema": "aiwf.loop/1", "workflow_id": "X", "current_phase": "plan"}),
        encoding="utf-8",
    )
    result = continue_workflow(tmp_path)
    assert result.status == "blocked"
    assert result.data.get("reason") == "WORKFLOW_STATE_NOT_FOUND"
