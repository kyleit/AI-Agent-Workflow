from pathlib import Path

from workflow_runtime.application.workflow.clarification_state import (
    validate_clarification_state,
)
from workflow_runtime.application.docs.artifact_validator import (
    validate_artifact_general,
)


def _write_state(root: Path, pending: dict, workflow: dict) -> None:
    (root / ".agents" / "runtime").mkdir(parents=True)
    (root / ".agents" / "state").mkdir(parents=True)
    import json

    (root / ".agents" / "runtime" / "pending-clarification.json").write_text(
        json.dumps(pending), encoding="utf-8"
    )
    (root / ".agents" / "state" / "workflow.json").write_text(
        json.dumps(workflow), encoding="utf-8"
    )


def test_unresolved_clarification_requires_bound_waiting_workflow(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        {"workflow_id": "FEAT-001", "classification": "BLOCKING", "status": "PENDING"},
        {"active_workflow": "FEAT-001", "active_phase": "brainstorming", "waiting_for": None},
    )

    result = validate_clarification_state(tmp_path)

    assert result["status"] == "BLOCKED"
    assert "unresolved_clarification_not_in_waiting_state" in result["blocking_findings"]


def test_resolved_clarification_cannot_survive_without_active_workflow(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        {"workflow_id": "FEAT-001", "classification": "RESOLVED", "status": "RESOLVED"},
        {"active_workflow": None, "active_phase": "implementation", "waiting_for": None},
    )

    result = validate_clarification_state(tmp_path)

    assert result["status"] == "BLOCKED"
    assert "resolved_clarification_without_active_workflow" in result["blocking_findings"]


def test_bound_resolved_clarification_must_have_left_waiting_state(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        {"workflow_id": "FEAT-001", "classification": "RESOLVED", "status": "RESOLVED"},
        {"active_workflow": "FEAT-001", "active_phase": "clarifying", "waiting_for": "owner_clarification"},
    )

    result = validate_clarification_state(tmp_path)

    assert result["status"] == "BLOCKED"
    assert "resolved_clarification_still_in_waiting_state" in result["blocking_findings"]


def test_no_pending_clarification_is_clear(tmp_path: Path) -> None:
    assert validate_clarification_state(tmp_path) == {
        "status": "CLEAR",
        "blocking_findings": [],
    }


def test_blocking_question_cannot_use_recommended_default_as_owner_answer(tmp_path: Path) -> None:
    question = tmp_path / "docs" / "features" / "monitor" / "questions" / "Q01_topology.md"
    question.parent.mkdir(parents=True)
    question.write_text(
        "---\nclassification: BLOCKING\nstatus: RESOLVED_DEFAULT_RECOMMENDED\n---\n"
        "## Decision\nOption 1 is recommended.\n",
        encoding="utf-8",
    )

    result = validate_clarification_state(tmp_path)

    assert result["status"] == "BLOCKED"
    assert "blocking_question_resolved_without_owner_evidence:docs/features/monitor/questions/Q01_topology.md" in result["blocking_findings"]


def test_artifact_validation_exposes_orphaned_clarification(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        {"workflow_id": "FEAT-001", "classification": "RESOLVED", "status": "RESOLVED"},
        {"active_workflow": None, "active_phase": "implementation", "waiting_for": None},
    )
    spec = tmp_path / "docs" / "requirements" / "feature_requirement_specification.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        "# Requirement Specification\n\n## Ambiguity And Decision Ledger\n",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(spec))

    assert result["status"] == "failure"
    assert "resolved_clarification_without_active_workflow" in result["blocking_findings"]
