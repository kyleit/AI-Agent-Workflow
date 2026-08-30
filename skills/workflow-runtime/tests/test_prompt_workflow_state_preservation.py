from __future__ import annotations

import json
from pathlib import Path

from workflow_runtime.application.verification import approval_gate
from workflow_runtime.application.workflow.workflow_entry_gateway import (
    WorkflowEntryGateway,
)


def test_read_only_workflow_state_write_preserves_active_state(tmp_path: Path) -> None:
    state = tmp_path / ".agents" / "state"
    state.mkdir(parents=True)
    path = state / "workflow.json"
    original = {
        "active_workflow": "FEAT-060",
        "active_phase": "blueprint",
        "work_item": {"id": "FEAT-060"},
        "blueprint": "docs/FEAT-060_blueprint.md",
    }
    path.write_text(json.dumps(original), encoding="utf-8")

    gateway = WorkflowEntryGateway(str(tmp_path))
    gateway._write_workflow_state(
        str(state), {"requested_action": "status"}, mutation=False,
    )

    result = json.loads(path.read_text(encoding="utf-8"))
    assert result["active_workflow"] == "FEAT-060"
    assert result["active_phase"] == "blueprint"
    assert result["work_item"] == {"id": "FEAT-060"}
    assert result["blueprint"] == "docs/FEAT-060_blueprint.md"


def test_response_for_changed_choice_context_is_blocked(
    tmp_path: Path, monkeypatch,
) -> None:
    runtime = tmp_path / ".agents" / "runtime"
    state = tmp_path / ".agents" / "state"
    runtime.mkdir(parents=True)
    state.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(approval_gate, "PENDING_CHOICE_FILE", str(runtime / "pending.json"))
    monkeypatch.setattr(approval_gate, "CHOICE_RESPONSE_FILE", str(runtime / "response.json"))
    (state / "workflow.json").write_text(
        json.dumps({"active_workflow": "FEAT-060"}), encoding="utf-8",
    )

    approval_gate.create_choice("blueprint_approval", "Approve", "", [])
    response = json.loads((runtime / "pending.json").read_text(encoding="utf-8"))
    response["context"]["workflow_id"] = "FEAT-999"
    (runtime / "response.json").write_text(json.dumps(response), encoding="utf-8")

    result = approval_gate.read_choice("blueprint_approval")
    assert result["status"] == "blocked"
    assert "choice_context_mismatch" in result["blocking_findings"]
