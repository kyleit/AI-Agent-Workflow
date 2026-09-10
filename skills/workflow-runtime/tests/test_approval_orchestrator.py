from __future__ import annotations

import hashlib
from pathlib import Path

from workflow_runtime.application.workflow.approval_orchestrator import (
    ApprovalOrchestrator,
)


def _validation(status: str, blueprint_sha256: str, result_id: str = "result-1"):
    return type(
        "Validation",
        (),
        {
            "status": status,
            "blueprint_sha256": blueprint_sha256,
            "source_snapshot": "git:test",
            "result_id": result_id,
        },
    )()


def test_stale_prompt_is_replaced_after_blueprint_hash_change(tmp_path: Path) -> None:
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text("version one", encoding="utf-8")
    first_hash = hashlib.sha256(blueprint.read_bytes()).hexdigest()
    first = ApprovalOrchestrator().prepare_user_approval(
        "FEAT-612", blueprint, _validation("APPROVAL_READY", first_hash)
    )

    blueprint.write_text("version two", encoding="utf-8")
    second_hash = hashlib.sha256(blueprint.read_bytes()).hexdigest()
    orchestrator = ApprovalOrchestrator()
    second = orchestrator.prepare_user_approval(
        "FEAT-612", blueprint, _validation("APPROVAL_READY", second_hash, "result-2")
    )

    assert second.blueprint_sha256 == second_hash
    assert second.validation_result_id == "result-2"
    stale = orchestrator.resume_after_approval("Approve implementation", first)
    assert stale.resumed is False
    assert stale.status == "STALE_PRESENTATION"


def test_approval_boundary_only_returns_bound_resume_or_cancel(tmp_path: Path) -> None:
    blueprint = tmp_path / "blueprint.md"
    blueprint.write_text("stable", encoding="utf-8")
    orchestrator = ApprovalOrchestrator()
    blueprint_hash = hashlib.sha256(blueprint.read_bytes()).hexdigest()
    presentation = orchestrator.prepare_user_approval(
        "FEAT-612", blueprint, _validation("APPROVAL_READY", blueprint_hash)
    )

    approved = orchestrator.resume_after_approval("Approve implementation", presentation)
    cancelled = orchestrator.resume_after_approval("Cancel", presentation)
    unavailable = orchestrator.handle_adapter_result("PROMPT_UNAVAILABLE", presentation)

    assert approved.resumed is True
    assert approved.status == "IMPLEMENTATION_ENTRY_PENDING"
    assert cancelled.status == "CANCELLED"
    assert unavailable.status == "PROMPT_UNAVAILABLE"
