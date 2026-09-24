"""Prove linked installs find the gate runner, and scope metrics read declarations.

Two counts are lowered in this batch, so each has a positive case proving the rule
it feeds still fires for a genuinely large artifact set.
"""

import json
from pathlib import Path

from workflow_runtime.application.workflow.blueprint_artifact_set_validator import (
    BlueprintArtifactSetValidator,
    _file_matrix_row_count,
)
from workflow_runtime.application.workflow.blueprint_authoring_policy_validator import (
    BlueprintAuthoringPolicyValidator,
)
from workflow_runtime.application.workflow.blueprint_scope_decomposer import (
    BlueprintScopeDecomposer,
)
from workflow_runtime.application.workflow.blueprint_validation_loop import (
    BlueprintAutoValidationService,
)
from workflow_runtime.application.workflow.runtime_link import linked_install_root

RUNNER = Path("skills") / "strict-code-block-gate" / "scripts" / "run_strict_code_block_gate.py"


def _link(workspace: Path, payload: object) -> None:
    descriptor = workspace / ".agents" / "runtime-link.json"
    descriptor.parent.mkdir(parents=True, exist_ok=True)
    descriptor.write_text(
        payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8"
    )


def _global_install(tmp_path: Path) -> Path:
    root = tmp_path / "global"
    runner = root / RUNNER
    runner.parent.mkdir(parents=True, exist_ok=True)
    runner.write_text("# runner\n", encoding="utf-8")
    return root


def test_linked_install_root_reads_the_descriptor(tmp_path: Path) -> None:
    global_root = _global_install(tmp_path)
    linked = tmp_path / "linked"
    _link(linked, {"bridge_mode": "global_link", "global_root": str(global_root)})
    assert linked_install_root(linked) == global_root

    copied = tmp_path / "copied"
    _link(copied, {"bridge_mode": "legacy_copy", "global_root": str(global_root)})
    assert linked_install_root(copied) is None

    malformed = tmp_path / "malformed"
    _link(malformed, "{not json")
    assert linked_install_root(malformed) is None

    assert linked_install_root(tmp_path / "absent") is None


def test_linked_project_finds_the_global_runner(tmp_path: Path) -> None:
    global_root = _global_install(tmp_path)
    workspace = tmp_path / "project"
    workspace.mkdir()
    _link(workspace, {"bridge_mode": "global_link", "global_root": str(global_root)})
    service = BlueprintAutoValidationService(workspace)
    found = next(c for c in service._gate_runner_candidates() if c.is_file())
    assert found == global_root / RUNNER


def test_project_runner_still_takes_precedence(tmp_path: Path) -> None:
    global_root = _global_install(tmp_path)
    workspace = tmp_path / "project"
    local = workspace / RUNNER
    local.parent.mkdir(parents=True)
    local.write_text("# local\n", encoding="utf-8")
    _link(workspace, {"bridge_mode": "global_link", "global_root": str(global_root)})
    service = BlueprintAutoValidationService(workspace)
    found = next(c for c in service._gate_runner_candidates() if c.is_file())
    assert found == workspace.resolve() / RUNNER


def test_authoring_validator_uses_the_shared_reader(tmp_path: Path) -> None:
    global_root = _global_install(tmp_path)
    workspace = tmp_path / "project"
    _link(workspace, {"bridge_mode": "global_link", "global_root": str(global_root)})
    assert BlueprintAuthoringPolicyValidator()._linked_install_root(workspace) == global_root


MATRIX = "\n".join([
    "## File-By-File Change Matrix",
    "",
    "| File | Operation | Code Block IDs |",
    "|---|---|---|",
    "| `pkg/a.py` | create | `B1` |",
    "| `pkg/b.py` | create | `B2` |",
])


def _task_table(rows: int) -> str:
    lines = ["## Implementation Task Contract", "",
             "| Task | Responsibility | Exact Change |", "|---|---|---|"]
    lines += [f"| `T{n}` | Own it | Add one import line |" for n in range(rows)]
    return "\n".join(lines)


def test_task_table_verbs_are_not_counted_as_files() -> None:
    text = MATRIX + "\n\n" + _task_table(9) + "\n"
    assert _file_matrix_row_count(text) == 2


def test_genuine_large_matrix_still_requires_subfeatures(tmp_path: Path) -> None:
    master = tmp_path / "master.md"
    master.write_text("# Master Blueprint\n", encoding="utf-8")
    rows = "\n".join(f"| `pkg/m{n}.py` | create | `B{n}` |" for n in range(9))
    phase = tmp_path / "fam" / "phase-01.md"
    phase.parent.mkdir()
    phase.write_text(
        "## File-By-File Change Matrix\n\n| File | Operation | Code Block IDs |\n"
        "|---|---|---|\n" + rows + "\n",
        encoding="utf-8",
    )
    result = BlueprintArtifactSetValidator().validate(master, [phase], {"recommended_phase_count": 1})
    assert "phase_subfeature_layout_required:fam:files=9" in result.blocking_findings

    small = tmp_path / "fam2" / "phase-01.md"
    small.parent.mkdir()
    small.write_text(MATRIX + "\n\n" + _task_table(9) + "\n", encoding="utf-8")
    result = BlueprintArtifactSetValidator().validate(master, [small], {"recommended_phase_count": 1})
    assert not [f for f in result.blocking_findings if f.startswith("phase_subfeature_layout_required")]


def test_acceptance_criteria_are_not_capabilities() -> None:
    text = "FR-01 FR-02 " + " ".join(f"AC-{n:02d}" for n in range(1, 9)) + " NFR-01 NFR-02"
    metrics = BlueprintScopeDecomposer().infer_from_blueprint(text)
    assert metrics["capability_count"] == 2


def test_committed_capabilities_still_drive_the_split() -> None:
    text = " ".join(f"FR-{n:02d}" for n in range(1, 9))
    decomposer = BlueprintScopeDecomposer()
    metrics = decomposer.infer_from_blueprint(text)
    assert metrics["capability_count"] == 8
    assessment = decomposer.assess(8, 0, 0, False)
    assert assessment.recommended_phase_count == 3
