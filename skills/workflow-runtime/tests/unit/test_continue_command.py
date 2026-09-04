from __future__ import annotations

import json

from workflow_runtime.presentation.cli.commands import build_registry
from workflow_runtime.presentation.cli.commands._impl.workflow.continuation import (
    continue_workflow,
)


def _write_state(root, payload: dict) -> None:
    state_dir = root / ".agents" / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "workflow.json").write_text(json.dumps(payload), encoding="utf-8")


def test_continue_is_registered() -> None:
    registry = build_registry()
    assert "continue" in registry._commands


def test_continue_returns_actionable_agent_envelope(tmp_path) -> None:
    _write_state(
        tmp_path,
        {
            "active_workflow": "FIX-429",
            "active_phase": "implementation",
            "suggested_next_skill": "blueprint-to-implementation",
            "suggested_next_command": "implement",
        },
    )

    result = continue_workflow(tmp_path, budget=8)

    assert result.status == "success"
    assert result.data["workflow_id"] == "FIX-429"
    assert result.next_action.automatic is True
    assert result.next_action.skill == "blueprint-to-implementation"


def test_continue_blocks_missing_state(tmp_path) -> None:
    result = continue_workflow(tmp_path)

    assert result.status == "blocked"
    assert result.data["reason"] == "WORKFLOW_STATE_NOT_FOUND"


def test_continue_blocks_approval_boundary(tmp_path) -> None:
    _write_state(
        tmp_path,
        {
            "active_workflow": "FIX-429",
            "active_phase": "blueprint",
            "waiting_for": "BLUEPRINT_APPROVAL",
        },
    )

    result = continue_workflow(tmp_path)

    assert result.status == "blocked"
    assert result.data["hard_stop"] is True
    assert result.next_action.requires_approval is True


def test_continue_rejects_invalid_budget(tmp_path) -> None:
    result = continue_workflow(tmp_path, budget=0)

    assert result.status == "invalid_input"
    assert result.data["reason"] == "INVALID_CONTINUATION_BUDGET"
