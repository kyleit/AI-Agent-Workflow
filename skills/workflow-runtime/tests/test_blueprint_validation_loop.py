from pathlib import Path

from workflow_runtime.application.workflow.blueprint_validation_loop import (
    BlueprintAutoValidationService,
)


_MARKERS = (
    "Document Control And Upstream Traceability",
    "Executive Architecture And 4-Layer DDD Topology",
    "Data Flow And Sequence Diagram",
    "File-By-File Change Matrix",
    "QA Verification Matrix",
    "Internal Review Evidence",
    "CODE_BLOCK_GATE",
    "Master Blueprint",
    "Phase Blueprint",
    "Feature Coverage Matrix",
    "declared_phase_count: 1",
)


def _blueprint_root(tmp_path: Path) -> Path:
    docs = tmp_path / "docs" / "features"
    docs.mkdir(parents=True)
    (docs / "FEAT-TEST_master.md").write_text("\n".join(_MARKERS), encoding="utf-8")
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
    assert "CODE_BLOCK_GATE:BLOCKED" in result.blocking_findings


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
