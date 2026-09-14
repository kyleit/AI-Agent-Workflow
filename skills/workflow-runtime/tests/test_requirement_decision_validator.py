from pathlib import Path

from workflow_runtime.application.docs.artifact_validator import validate_artifact_general
from workflow_runtime.application.workflow.workflow_entry_gateway import (
    WorkflowEntryGateway,
    build_owner_clarification,
)


def test_requirement_spec_blocks_inferred_high_impact_decisions(tmp_path: Path):
    spec = tmp_path / "docs" / "requirements" / "feature_req_spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        """# Requirement Specification

## Ambiguity And Decision Ledger
| Item | Source | Classification | Owner Decision | Impact | Downstream Artifacts |
|---|---|---|---|---|---|
| Probe mode | Prompt | NON_BLOCKING | Hybrid chosen by AI | Backend and runtime | Blueprint |
""",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(spec))

    assert result["status"] == "failure"
    assert "requirement_high_impact_inferred_as_non_blocking:row_2" in result["blocking_findings"]


def test_requirement_spec_allows_explicit_hard_constraint(tmp_path: Path):
    spec = tmp_path / "docs" / "requirements" / "feature_req_spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        """# Requirement Specification

## Ambiguity And Decision Ledger
| Item | Source | Classification | Owner Decision | Impact | Downstream Artifacts |
|---|---|---|---|---|---|
| Database | Prompt | NON_BLOCKING | SQLite3 is an explicitly specified hard constraint | Data schema | Blueprint |
""",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(spec))

    assert result["status"] == "success"


def test_blocking_owner_claim_requires_bound_response_evidence(tmp_path: Path):
    spec = tmp_path / "docs" / "requirements" / "feature_req_spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        """# Requirement Specification

## Ambiguity And Decision Ledger
| Item | Source | Classification | Owner Decision | Impact | Downstream Artifacts |
|---|---|---|---|---|---|
| Runtime mode | Prompt | BLOCKING | Confirmed by owner: hybrid | scope, runtime, data | Blueprint |
""",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(spec))

    assert result["status"] == "failure"
    assert "requirement_owner_confirmation_evidence_missing:row_2" in result["blocking_findings"]


def test_owner_clarification_requires_current_question_option_and_answer(tmp_path: Path):
    spec = tmp_path / "docs" / "requirements" / "feature_req_spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        """# Requirement Specification

## Ambiguity And Decision Ledger
| Item | Source | Classification | Owner Decision | Impact | Downstream Artifacts |
|---|---|---|---|---|---|
| Runtime mode | Interactive Clarification | BLOCKING | Confirmed by owner: Hybrid. owner-response-id: resp-1 | scope, runtime | Blueprint |
""",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(spec))

    assert result["status"] == "failure"
    assert "requirement_clarification_transaction_capture_missing:row_2" in result["blocking_findings"]


def test_mixed_prompt_and_best_practice_cannot_hide_high_impact_assumption(tmp_path: Path):
    spec = tmp_path / "docs" / "requirements" / "feature_req_spec.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        """# Requirement Specification

## Ambiguity And Decision Ledger
| Item | Source | Classification | Owner Decision | Impact | Downstream Artifacts |
|---|---|---|---|---|---|
| Probe cadence | Prompt & Best Practice | NON_BLOCKING | Default 10 seconds confirmed by owner as standard | runtime, backend, acceptance | Blueprint |
""",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(spec))

    assert result["status"] == "failure"
    assert "requirement_high_impact_inferred_as_non_blocking:row_2" in result["blocking_findings"]


def test_blocking_question_reference_without_owner_response_is_rejected(tmp_path: Path):
    spec = tmp_path / "docs" / "features" / "monitor" / "specifications" / "req.md"
    spec.parent.mkdir(parents=True)
    spec.write_text(
        """# Requirement Specification

## Ambiguity And Decision Ledger
| Item | Source | Classification | Owner Decision | Impact | Downstream Artifacts |
|---|---|---|---|---|---|
| Monitoring mode | Interactive Clarification | BLOCKING | Option 1 selected through Q01 | runtime, data | Blueprint |
""",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(spec))

    assert result["status"] == "failure"
    assert "requirement_blocking_owner_evidence_missing:row_2" in result["blocking_findings"]


def test_resolved_markdown_question_requires_owner_response(tmp_path: Path):
    question = tmp_path / "docs" / "features" / "monitor" / "questions" / "Q01_mode.md"
    question.parent.mkdir(parents=True)
    question.write_text(
        """# Q01

**Status**: `RESOLVED`

## Decision
The recommended option was selected.
""",
        encoding="utf-8",
    )

    result = validate_artifact_general(str(question))

    assert result["status"] == "failure"
    assert any("clarification_resolved_without_owner_response" in item for item in result["blocking_findings"])


def test_greenfield_request_requires_owner_clarification(tmp_path: Path, monkeypatch):
    request = "Xây dựng một ứng dụng quản lý tài liệu từ đầu"
    clarification = build_owner_clarification(request)

    assert clarification is not None
    assert clarification["classification"] == "BLOCKING"
    assert len(clarification["options"]) == 2
    assert all("agentless" not in str(option).lower() for option in clarification["options"])

    monkeypatch.setattr(
        "workflow_runtime.application.workflow.workflow_entry_gateway.ensure_project_memory",
        lambda _root: type("Memory", (), {"status": "cached", "files_changed": 0})(),
    )
    monkeypatch.setattr(
        "workflow_runtime.application.workflow.workflow_entry_gateway.build_agent_context",
        lambda *_args, **_kwargs: type("Context", (), {})(),
    )
    result = WorkflowEntryGateway(str(tmp_path)).handle_request(request)

    assert result["status"] == "CLARIFICATION_REQUIRED"
    assert result["requires_user_input"] is True
    assert result["current_phase"] == "clarifying"
    assert result["next_skill"] == "raw-intent-normalization"
    assert not list((tmp_path / "docs").rglob("*")) if (tmp_path / "docs").exists() else True
    state = (tmp_path / ".agents" / "state" / "workflow.json").read_text(encoding="utf-8")
    assert "WAITING_FOR_OWNER" in state
    assert (tmp_path / ".agents" / "runtime" / "pending-clarification.json").exists()
