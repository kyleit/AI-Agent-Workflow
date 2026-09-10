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
