from pathlib import Path

from workflow_runtime.application.docs import artifact_validator
from workflow_runtime.application.workflow.blueprint_validation_loop import (
    BlueprintValidationResult,
)


def _write_semantic_blueprint(root: Path) -> Path:
    path = root / "docs" / "features" / "demo" / "blueprints" / "FEAT-001_demo_blueprint.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        """---
artifact_type: technical_blueprint
feature_id: FEAT-001
workflow: standard-development
status: draft
---
# Summary
# Scope
# Technical Design
# Files to Change
# Implementation Steps
# Validation Plan
# Rollback Plan
## Document Control And Upstream Traceability
## Executive Architecture And 4-Layer DDD Topology
## Data Flow And Sequence Diagram
```mermaid
sequenceDiagram
  User->>System: request
```
## File-By-File Change Matrix
## QA Verification Matrix
## Internal Review Evidence
## CODE_BLOCK_GATE
""",
        encoding="utf-8",
    )
    (root / ".git").mkdir()
    return path


def test_semantic_validate_uses_strict_approval_loop(tmp_path: Path, monkeypatch) -> None:
    blueprint = _write_semantic_blueprint(tmp_path)
    expected = BlueprintValidationResult(
        status="BLOCKED",
        score=0,
        blocking_findings=["feature_coverage_matrix_missing"],
        evidence=["docs/aiwf-runs/FEAT-001/05-blueprint/code-block-gate.json"],
    )
    monkeypatch.setattr(
        "workflow_runtime.application.workflow.blueprint_validation_loop"
        ".BlueprintAutoValidationService.validate_for_approval",
        lambda *_args, **_kwargs: expected,
    )

    result = artifact_validator.validate_blueprint_file(str(blueprint))

    assert result["status"] == "failure"
    assert result["blocking_findings"] == ["feature_coverage_matrix_missing"]


def test_semantic_validate_accepts_absolute_project_path(tmp_path: Path, monkeypatch) -> None:
    blueprint = _write_semantic_blueprint(tmp_path)
    expected = BlueprintValidationResult(
        status="APPROVAL_READY",
        score=100,
        evidence=[],
    )
    monkeypatch.setattr(
        "workflow_runtime.application.workflow.blueprint_validation_loop"
        ".BlueprintAutoValidationService.validate_for_approval",
        lambda *_args, **_kwargs: expected,
    )

    result = artifact_validator.validate_blueprint_file(str(blueprint.resolve()))

    assert result["status"] == "success"
    assert result["score"] == 100


def test_semantic_validate_rejects_agent_authored_approval_without_state(tmp_path: Path) -> None:
    blueprint = _write_semantic_blueprint(tmp_path)
    content = blueprint.read_text(encoding="utf-8").replace("status: draft", "status: APPROVED")
    blueprint.write_text(content, encoding="utf-8")

    result = artifact_validator.validate_blueprint_file(str(blueprint))

    assert result["status"] == "failure"
    assert result["blocking_findings"] == ["unbound_blueprint_approval_claim"]
