from pathlib import Path

from workflow_runtime.application.workflow.blueprint_validation_loop import (
    BlueprintAutoValidationService,
)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    has_bound_owner_blueprint_approval,
)


_MARKERS = (
    "## Document Control And Upstream Traceability",
    "## Executive Architecture And 4-Layer DDD Topology",
    "## Data Flow And Sequence Diagram",
    "## File-By-File Change Matrix",
    "## QA Verification Matrix",
    "## Internal Review Evidence",
    "## CODE_BLOCK_GATE",
    "## Master Blueprint",
    "## Phase Blueprint",
    "## Feature Coverage Matrix",
    "declared_phase_count: 1",
)


def _blueprint_root(tmp_path: Path) -> Path:
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "FEAT-TEST_master.md").write_text(
        "\n".join(_MARKERS)
        + "\n```mermaid\nsequenceDiagram\n  User->>System: request\n```\n",
        encoding="utf-8",
    )
    (docs / "FEAT-TEST-P01_phase.md").write_text(
        "phase_id: P01\nPhase Scope\nFile-By-File Change Matrix\n"
        "Implementation-Ready Code-Block Inventory\nQA Verification Matrix\nNO-GO Conditions\n",
        encoding="utf-8",
    )
    return tmp_path


def test_clean_blueprint_is_approval_ready(tmp_path: Path, monkeypatch) -> None:
    root = _blueprint_root(tmp_path)
    service = BlueprintAutoValidationService(root)
    monkeypatch.setattr(service, "_run_code_block_gate", lambda *_args: {
        "decision": "PASS",
        "blueprint_full_sha256": "test-hash",
        "per_code_block": [],
        "blocking_findings": [],
    })

    result = service.validate_for_approval(
        root / "docs" / "features" / "FEAT-TEST_master.md", "FEAT-TEST"
    )

    assert result.status == "APPROVAL_READY"


def test_post_implementation_validation_returns_verified_status(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = _blueprint_root(tmp_path)
    service = BlueprintAutoValidationService(root)
    monkeypatch.setattr(service, "_run_code_block_gate", lambda *_args: {
        "decision": "PASS",
        "blueprint_full_sha256": "test-hash",
        "per_code_block": [],
        "blocking_findings": [],
    })

    result = service.validate_for_approval(
        root / "docs" / "features" / "FEAT-TEST_master.md",
        "FEAT-TEST",
        post_implementation=True,
    )

    assert result.status == "VERIFIED"
    assert result.next_action == "debug-to-verify"
    assert result.blocking_findings == []


def test_failed_code_block_gate_blocks_approval(tmp_path: Path, monkeypatch) -> None:
    root = _blueprint_root(tmp_path)
    service = BlueprintAutoValidationService(root)
    monkeypatch.setattr(service, "_run_code_block_gate", lambda *_args: {
        "decision": "BLOCKED",
        "blueprint_full_sha256": "test-hash",
        "per_code_block": [{"id": "B01", "status": "BLOCKED"}],
        "blocking_findings": ["invalid_block"],
    })

    result = service.validate_for_approval(
        root / "docs" / "features" / "FEAT-TEST_master.md", "FEAT-TEST"
    )

    assert result.status == "BLOCKED"


def test_agent_authored_approval_status_blocks_every_verify_route(tmp_path: Path, monkeypatch) -> None:
    blueprint = tmp_path / "docs" / "features" / "demo" / "blueprints" / "FEAT-001_demo_blueprint.md"
    blueprint.parent.mkdir(parents=True)
    blueprint.write_text(
        "---\nfeature_id: FEAT-001\nstatus: APPROVED\n---\n"
        "## Document Control And Upstream Traceability\n"
        "## Executive Architecture And 4-Layer DDD Topology\n"
        "## Data Flow And Sequence Diagram\n```mermaid\nsequenceDiagram\nA->>B: C\n```\n"
        "## File-By-File Change Matrix\n## QA Verification Matrix\n"
        "## Internal Review Evidence\n## CODE_BLOCK_GATE\n",
        encoding="utf-8",
    )
    (tmp_path / ".git").mkdir()
    (tmp_path / ".agents" / "state").mkdir(parents=True)
    monkeypatch.setattr(
        "workflow_runtime.application.workflow.blueprint_validation_loop.BlueprintAutoValidationService._run_code_block_gate",
        lambda *_args, **_kwargs: {"decision": "PASS", "blueprint_full_sha256": ""},
    )

    result = BlueprintAutoValidationService(tmp_path).validate_for_approval(blueprint, "FEAT-001")

    assert result.status == "BLOCKED"
    assert "unbound_blueprint_approval_claim" in result.blocking_findings


def test_verify_mode_allows_implemented_create_blocks_and_ignores_code_fence_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = _blueprint_root(tmp_path)
    target = root / "src" / "created.py"
    target.parent.mkdir()
    target.write_text("VALUE = 1\n", encoding="utf-8")
    blueprint = root / "docs" / "features" / "FEAT-TEST_master.md"
    blueprint.write_text(
        blueprint.read_text(encoding="utf-8")
        + "\n```python\npath = 'C:/generated/example.py'\n```\n",
        encoding="utf-8",
    )
    service = BlueprintAutoValidationService(root)
    monkeypatch.setattr(service, "_run_code_block_gate", lambda *_args: {
        "decision": "PASS",
        "blueprint_full_sha256": "test-hash",
        "per_code_block": [{
            "id": "B01",
            "implementation_ready": True,
            "operation": "create",
            "file": "src/created.py",
        }],
        "blocking_findings": [],
    })

    result = service.validate_for_approval(
        blueprint,
        "FEAT-TEST",
        allow_existing_creates=True,
    )

    assert result.status == "APPROVAL_READY"




def test_large_blueprint_requires_each_requirement_in_coverage_rows(tmp_path: Path) -> None:
    service = BlueprintAutoValidationService(tmp_path)
    text = """
## Master Blueprint
Scope includes FR-001 and FR-002.
## Phase Blueprint
## Feature Coverage Matrix
| Capability ID | Acceptance Criteria | Phase | Files | Code Blocks | Test IDs | Evidence Paths |
|---|---|---|---|---|---|---|
| FR-001 | visible result | P01 | src/app.go | B01 | T01 | docs/evidence/t01.log |
"""

    findings = service._scope_findings(
        text,
        {
            "capability_count": 4,
            "file_family_count": 0,
            "task_count": 0,
            "cross_layer": False,
            "recommended_phase_count": 2,
        },
        None,
    )

    assert "feature_coverage_missing:FR-001" not in findings
    assert "feature_coverage_missing:FR-002" in findings


def test_scope_metrics_cannot_reduce_complexity_inferred_from_blueprint(tmp_path: Path) -> None:
    service = BlueprintAutoValidationService(tmp_path)
    text = "\n".join(
        [
            "FR-001 FR-002 FR-003 FR-004",
            "| a | b | NEW |",
            "| c | d | MODIFY |",
            "| e | f | NEW |",
            "| 1 | task |",
            "| 2 | task |",
            "| 3 | task |",
            "| 4 | task |",
            "| 5 | task |",
            "| 6 | task |",
            "Domain Application Infrastructure Presentation",
        ]
    )

    metrics = service._scope_metrics(
        {"capability_count": 0, "file_family_count": 0, "task_count": 0, "cross_layer": False},
        text,
    )

    assert metrics["capability_count"] == 4
    assert metrics["file_family_count"] == 3
    assert metrics["task_count"] == 6
    assert metrics["cross_layer"] is True
    assert metrics["recommended_phase_count"] == 2


def test_preimplementation_runtime_pass_claims_are_blocked(tmp_path: Path) -> None:
    service = BlueprintAutoValidationService(tmp_path)
    text = """
| Go Fiber API readiness | real health response | PASS |
| Architecture boundaries | four layers | PASS |
| Desktop shell | Wails startup | PASS |
"""

    findings = service._preimplementation_runtime_pass_findings(text, "master")

    assert findings == [
        "preimplementation_runtime_pass_claim:master",
        "preimplementation_runtime_pass_claim:master",
    ]


def test_static_readiness_pass_rows_are_not_runtime_evidence(tmp_path: Path) -> None:
    service = BlueprintAutoValidationService(tmp_path)
    text = """
## Section 10: Blueprint Readiness Assessment And CODE_BLOCK_GATE
| Phase Count Derived From Complexity | PASS (3 delivery families: backend, frontend, wails) |
| Checklist Result | PASS (complete custom controls) |
## QA Verification Matrix
| TEST-01 | Wails startup runtime | PASS |
"""

    findings = service._preimplementation_runtime_pass_findings(text, "master")

    assert findings == ["preimplementation_runtime_pass_claim:master"]


def test_upstream_plan_and_roadmap_scope_cannot_be_silently_dropped(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "features" / "demo"
    (docs / "blueprints" / "backend" / "storage").mkdir(parents=True)
    (docs / "roadmaps").mkdir()
    (docs / "plans").mkdir()
    master = docs / "blueprints" / "FEAT-001_demo_blueprint.md"
    phase = docs / "blueprints" / "backend" / "storage" / "FEAT-001_P01_storage.md"
    master.write_text(
        "linked_artifacts:\n"
        "  roadmap: docs/features/demo/roadmaps/FEAT-001_roadmap.md\n"
        "  plan: docs/features/demo/plans/FEAT-001_plan.md\n",
        encoding="utf-8",
    )
    phase.write_text("phase_id: P01\n", encoding="utf-8")
    (docs / "roadmaps" / "FEAT-001_roadmap.md").write_text(
        "| `P01-BACKEND-BASE` | Backend |\n"
        "| `P02-PROBER-ENGINE` | Prober |\n",
        encoding="utf-8",
    )
    (docs / "plans" / "FEAT-001_plan.md").write_text(
        "- `go.mod`\n- `internal/prober/prober.go`\n",
        encoding="utf-8",
    )

    findings = BlueprintAutoValidationService(tmp_path)._upstream_delivery_coverage_findings(
        master.read_text(encoding="utf-8"), master, [phase]
    )

    assert "upstream_delivery_unit_coverage_matrix_missing" in findings
    assert "upstream_plan_file_unmaterialized:internal/prober/prober.go" in findings


def test_upstream_delivery_matrix_must_point_to_distinct_discovered_phases(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "features" / "demo"
    (docs / "blueprints" / "backend").mkdir(parents=True)
    (docs / "roadmaps").mkdir()
    (docs / "plans").mkdir()
    master = docs / "blueprints" / "FEAT-001_demo_blueprint.md"
    phase = docs / "blueprints" / "backend" / "FEAT-001_P01_backend.md"
    master.write_text(
        "linked_artifacts:\n"
        "  roadmap: docs/features/demo/roadmaps/FEAT-001_roadmap.md\n"
        "## Upstream Delivery Unit Coverage Matrix\n"
        "| Upstream Phase | Blueprint Artifact |\n"
        "| `P01-BACKEND-BASE` | `docs/features/demo/blueprints/backend/FEAT-001_P01_backend.md` |\n"
        "| `P02-PROBER-ENGINE` | `docs/features/demo/blueprints/backend/FEAT-001_P01_backend.md` |\n",
        encoding="utf-8",
    )
    phase.write_text("phase_id: P01\n", encoding="utf-8")
    (docs / "roadmaps" / "FEAT-001_roadmap.md").write_text(
        "`P01-BACKEND-BASE`\n`P02-PROBER-ENGINE`\n",
        encoding="utf-8",
    )

    findings = BlueprintAutoValidationService(tmp_path)._upstream_delivery_coverage_findings(
        master.read_text(encoding="utf-8"), master, [phase]
    )

    assert "upstream_phase_artifact_count_mismatch:required=2:mapped=1" in findings


def test_blueprint_approve_requires_bound_owner_prompt_response(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runtime = tmp_path / ".agents" / "runtime"
    runtime.mkdir(parents=True)

    assert has_bound_owner_blueprint_approval(
        "FEAT-001", "docs/features/demo/blueprints/FEAT-001_blueprint.md"
    ) is False

    (runtime / "pending-choice.json").write_text(
        '{"id":"blueprint_approval","context":{"work_item_id":"FEAT-001"}}',
        encoding="utf-8",
    )
    (runtime / "choice-response.json").write_text(
        '{"id":"blueprint_approval","selected":"approve"}',
        encoding="utf-8",
    )

    assert has_bound_owner_blueprint_approval(
        "FEAT-001", "docs/features/demo/blueprints/FEAT-001_blueprint.md"
    ) is True
