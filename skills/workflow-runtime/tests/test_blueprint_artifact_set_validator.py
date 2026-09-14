from pathlib import Path

from workflow_runtime.application.workflow.blueprint_artifact_set_validator import (
    BlueprintArtifactSetValidator,
)


def test_phase_count_and_required_markers_are_checked(tmp_path: Path) -> None:
    master = tmp_path / "master.md"
    master.write_text("master", encoding="utf-8")
    phase = tmp_path / "FEAT-P01_phase.md"
    phase.write_text(
        "phase_id: P01\nPhase Scope\nFile-By-File Change Matrix\n"
        "Implementation-Ready Code-Block Inventory\nQA Verification Matrix\nNO-GO Conditions\n",
        encoding="utf-8",
    )

    result = BlueprintArtifactSetValidator().validate(
        master, [phase], {"recommended_phase_count": 1}
    )

    assert result.passed is True


def test_single_bounded_master_does_not_require_fake_phase(tmp_path: Path) -> None:
    master = tmp_path / "master.md"
    master.write_text("master", encoding="utf-8")

    result = BlueprintArtifactSetValidator().validate(
        master, [], {"recommended_phase_count": 1}
    )

    assert result.passed is True


def test_phase_blueprints_are_discovered_recursively(tmp_path: Path) -> None:
    master = tmp_path / "FEAT-001_master.md"
    master.write_text("master", encoding="utf-8")
    phase_dir = tmp_path / "phase-01-backend"
    phase_dir.mkdir()
    phase = phase_dir / "FEAT-001-P01_backend.md"
    phase.write_text(
        "phase_id: P01\nPhase Scope\nFile-By-File Change Matrix\n"
        "Implementation-Ready Code-Block Inventory\nQA Verification Matrix\n"
        "NO-GO Conditions\n",
        encoding="utf-8",
    )

    from workflow_runtime.application.workflow.blueprint_validation_loop import (
        BlueprintAutoValidationService,
    )

    discovered = BlueprintAutoValidationService(tmp_path)._discover_phase_paths(master)

    assert discovered == [phase]


def test_large_artifact_set_requires_executable_task_contract(tmp_path: Path) -> None:
    master = tmp_path / "master.md"
    master.write_text("# Master Blueprint\n", encoding="utf-8")
    phase = tmp_path / "backend" / "FEAT-001-P01_backend.md"
    phase.parent.mkdir()
    phase.write_text(
        "phase_id: P01\nPhase Scope\nFile-By-File Change Matrix\n"
        "Implementation-Ready Code-Block Inventory\nQA Verification Matrix\n"
        "NO-GO Conditions\n",
        encoding="utf-8",
    )

    result = BlueprintArtifactSetValidator().validate(
        master, [phase], {"recommended_phase_count": 2}
    )

    assert "master_implementation_task_contract_missing_or_incomplete" in result.blocking_findings
    assert any(
        item.startswith("phase_implementation_task_contract_missing_or_incomplete:")
        for item in result.blocking_findings
    )


def test_blueprint_length_never_blocks_without_size_note(tmp_path: Path) -> None:
    master = tmp_path / "master.md"
    master.write_text("\n".join(["# Master Blueprint"] * 1001), encoding="utf-8")

    result = BlueprintArtifactSetValidator().validate(
        master, [], {"recommended_phase_count": 1}
    )

    assert result.passed is True


def test_cohesive_blueprint_may_exceed_any_soft_guideline(tmp_path: Path) -> None:
    master = tmp_path / "master.md"
    master.write_text(
        "# Master Blueprint\n## Blueprint Size Decision\n"
        "Physical Lines: 1100\nSoft Guideline: around 1000\n"
        "AI Decision: keep cohesive\nCohesive Boundary: one contract\n"
        "Alternatives Rejected: mechanical split\n"
        "Rationale: splitting would separate the contract and implementation.\n"
        + "\n".join(["detail"] * 1001),
        encoding="utf-8",
    )

    result = BlueprintArtifactSetValidator().validate(
        master, [], {"recommended_phase_count": 1}
    )

    assert result.passed is True
