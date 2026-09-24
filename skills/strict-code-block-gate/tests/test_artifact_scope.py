"""Prove a gate run judges exactly one work item's documents.

Discovery is narrowed here, so the positive cases matter as much as the negative
ones: a genuine phase that stops being discovered would silently escape validation.
"""

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _module(name: str):
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _phase(master_reference: str = "") -> str:
    if not master_reference:
        return "# Phase\n"
    return (
        "---\nartifact_type: phase_blueprint\n"
        f"master_blueprint: {master_reference}\n---\n\n# Phase\n"
    )


def _root(tmp_path: Path) -> Path:
    return tmp_path / "docs" / "features" / "vir" / "blueprints"


def test_flat_sibling_masters_are_not_phases(tmp_path: Path) -> None:
    runner = _module("run_strict_code_block_gate")
    root = _root(tmp_path)
    master = _write(root / "FEAT-A_master_blueprint.md", "# A\n")
    for name in ("FEAT-B_master_blueprint.md", "FEAT-C_master_blueprint.md", "README.md"):
        _write(root / name, "# other\n")
    assert runner.discover_phase_paths(master) == []


def test_subdirectory_phase_is_still_discovered(tmp_path: Path) -> None:
    runner = _module("run_strict_code_block_gate")
    root = _root(tmp_path)
    master = _write(root / "FEAT-A_master_blueprint.md", "# A\n")
    phase = _write(root / "fam" / "P01_core.md", _phase())
    assert runner.discover_phase_paths(master) == [phase.resolve()]


def test_phase_declaring_another_master_is_excluded(tmp_path: Path) -> None:
    runner = _module("run_strict_code_block_gate")
    root = _root(tmp_path)
    master = _write(root / "FEAT-A_master_blueprint.md", "# A\n")
    _write(root / "FEAT-B_master_blueprint.md", "# B\n")
    mine = _write(root / "fam" / "phase-01.md", _phase("../FEAT-A_master_blueprint.md"))
    theirs = _write(root / "fam" / "phase-02.md", _phase("../FEAT-B_master_blueprint.md"))
    found = runner.discover_phase_paths(master)
    assert mine.resolve() in found
    assert theirs.resolve() not in found


def test_flat_document_declaring_this_master_is_included(tmp_path: Path) -> None:
    runner = _module("run_strict_code_block_gate")
    root = _root(tmp_path)
    master = _write(root / "FEAT-A_master_blueprint.md", "# A\n")
    flat = _write(root / "FEAT-A_phase_notes.md", _phase("FEAT-A_master_blueprint.md"))
    assert flat.resolve() in runner.discover_phase_paths(master)


def test_master_folder_scopes_to_blueprints_directory(tmp_path: Path) -> None:
    runner = _module("run_strict_code_block_gate")
    root = _root(tmp_path)
    master = _write(root / "master" / "FEAT-A_master_blueprint.md", "# A\n")
    _write(root / "master" / "FEAT-B_master_blueprint.md", "# B\n")
    phase = _write(root / "phase-01-core" / "phase-blueprint.md", _phase())
    assert runner.discover_phase_paths(master) == [phase.resolve()]


def test_master_folder_location_is_accepted(tmp_path: Path) -> None:
    runner = _module("run_strict_code_block_gate")
    nested = tmp_path / "docs/features/fx/blueprints/master/FEAT-A_master_blueprint.md"
    flat = tmp_path / "docs/features/fx/blueprints/FEAT-A_master_blueprint.md"
    assert runner.validate_blueprint_location(tmp_path, nested) == []
    assert runner.validate_blueprint_location(tmp_path, flat) == []


def test_root_location_is_still_rejected(tmp_path: Path) -> None:
    runner = _module("run_strict_code_block_gate")
    assert runner.validate_blueprint_location(tmp_path, tmp_path / "FEAT-A.md") == [
        "blueprint_location_invalid:FEAT-A.md"
    ]


def test_scratch_missing_finding_is_relative(tmp_path: Path) -> None:
    spike = _module("validate_spike_verified_blueprint")
    blueprint = _write(
        tmp_path / "docs/features/fx/blueprints/master.md",
        "---\nsource_verification_branch: B\nblueprint_depth: CONTRACT\n---\n\n# M\n",
    )
    result = spike.validate(blueprint, [], project_root=tmp_path, workflow_id="FX-1")
    scratch = [f for f in result["blocking_findings"] if f.startswith("greenfield_scratch_missing")]
    assert scratch == ["greenfield_scratch_missing:.agents/scratch/FX-1"]
