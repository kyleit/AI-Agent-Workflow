from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from workflow_runtime.application.command_contract import CommandResult, NextAction


def _read_object(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _load_continuation_state(root: Path) -> tuple[dict[str, Any], str]:
    workflow = _read_object(root / ".agents" / "state" / "workflow.json")
    if workflow is not None:
        runtime = _read_object(root / ".agents" / "state" / "runtime.json") or {}
        merged = dict(workflow)
        for key, value in runtime.items():
            merged.setdefault(key, value)
        return merged, "workflow"

    runtime = _read_object(root / ".agents" / "state" / "runtime.json")
    if runtime is not None:
        return runtime, "runtime"

    legacy = _read_object(root / ".agents" / ".session.json")
    return legacy or {}, "legacy"


def continue_workflow(root: Path, budget: int = 32) -> CommandResult:
    if budget < 1 or budget > 256:
        return CommandResult(
            command="continue",
            status="invalid_input",
            summary="Continuation budget must be between 1 and 256.",
            data={"reason": "INVALID_CONTINUATION_BUDGET", "budget": budget},
        )

    state, state_source = _load_continuation_state(root)
    raw_work_item = state.get("work_item")
    work_item = raw_work_item if isinstance(raw_work_item, dict) else {}
    workflow_id = str(state.get("active_workflow") or work_item.get("id") or "")
    phase = str(state.get("active_phase") or state.get("phase") or "")
    skill = str(
        state.get("suggested_next_skill")
        or state.get("current_skill")
        or state.get("next_skill")
        or ""
    )
    command = str(
        state.get("suggested_next_command")
        or state.get("current_command")
        or state.get("next_command")
        or ""
    )
    waiting_for = str(state.get("waiting_for") or "")

    if not workflow_id or not phase:
        return CommandResult(
            command="continue",
            status="blocked",
            summary="No active workflow state was found.",
            data={
                "reason": "WORKFLOW_STATE_NOT_FOUND",
                "hard_stop": True,
                "state_source": state_source,
            },
        )

    if waiting_for or bool(state.get("requires_approval")):
        reason = waiting_for or "APPROVAL_REQUIRED"
        return CommandResult(
            command="continue",
            status="blocked",
            summary="Workflow continuation stopped at an approval boundary.",
            data={
                "reason": reason,
                "hard_stop": True,
                "workflow_id": workflow_id,
                "phase": phase,
                "state_source": state_source,
            },
            next_action=NextAction(
                command="approve",
                required=True,
                requires_approval=True,
            ),
        )

    if not skill or not command:
        return CommandResult(
            command="continue",
            status="blocked",
            summary="Active workflow has no actionable next skill.",
            data={
                "reason": "NEXT_ACTION_UNAVAILABLE",
                "hard_stop": True,
                "workflow_id": workflow_id,
                "phase": phase,
                "state_source": state_source,
            },
        )

    return CommandResult(
        command="continue",
        status="success",
        summary="Active workflow continuation is ready for the AI agent.",
        data={
            "workflow_id": workflow_id,
            "phase": phase,
            "budget": budget,
            "hard_stop": False,
            "state_source": state_source,
        },
        next_action=NextAction(skill=skill, command=command, automatic=True),
    )


__all__ = ["continue_workflow"]
