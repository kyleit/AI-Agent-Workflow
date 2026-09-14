import importlib.util
from pathlib import Path


_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_artifact_set_code_blocks.py"
_SPEC = importlib.util.spec_from_file_location("validate_artifact_set_code_blocks", _SCRIPT)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
validate_artifact_set = _MODULE.validate_artifact_set


def test_large_single_blueprint_requires_phase_artifacts(tmp_path: Path) -> None:
    content = """# Master Blueprint\n\n## File-By-File Change Matrix\n\n| File Path | Code Block ID | Projected Lines | Owner | Imports | Exports | Exact Signatures | Commands | Tests | Evidence |\n|---|---|---:|---|---|---|---|---|---|---|\n""" + "\n".join(
        f"| backend/file{i}.go | block-{i} | 20 | backend | none | API | func File{i}() | go test ./... | test{i} | receipt |"
        for i in range(8)
    )
    path = tmp_path / "master_blueprint.md"
    path.write_text(content, encoding="utf-8")

    findings = validate_artifact_set([path], [{"blocks": []}])

    assert "artifact_set_phase_blueprints_missing" in findings


def test_path_header_is_not_confused_with_profile_header(tmp_path: Path) -> None:
    content = """# Master Blueprint

## File-By-File Change Matrix
| Path | Layer | Operation | Owner | Imports | Exports | Exact Signatures | Lines | Profile | Commands | Code Blocks | Tests | Evidence |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|
| frontend/src/Input.svelte | Frontend | create | ui | svelte | Input | export let value | 3 | svelte-strict-v1 | npm run build | block-input | TEST-1 | receipt |

## Master Blueprint
## Feature Coverage Matrix
## Project Initialization Coverage Matrix
"""
    path = tmp_path / "master_blueprint.md"
    path.write_text(content, encoding="utf-8")

    findings = validate_artifact_set([path], [{"blocks": []}])

    assert not any("svelte-strict-v1" in finding for finding in findings)
    assert "file_matrix_unknown_code_block:frontend/src/Input.svelte:block-input" in findings


def test_large_family_file_inventory_requires_small_feature_directory(tmp_path: Path) -> None:
    root = tmp_path / "blueprints"
    family = root / "backend"
    family.mkdir(parents=True)
    master = root / "master_blueprint.md"
    master.write_text("# Master Blueprint\n## Data Flow And Sequence Diagram\n", encoding="utf-8")
    phase = family / "P01_backend.md"
    rows = "\n".join(
        f"| file{i}.go | backend | create | owner | pkg | API | func File{i}() | 10 | go | go test | B{i} | T{i} | E{i} |"
        for i in range(9)
    )
    phase.write_text(
        """---
artifact_type: phase_blueprint
phase_id: P01
---
## Phase Scope
## File-By-File Change Matrix
| Path | Layer | Operation | Owner | Imports | Exports | Exact Signatures | Lines | Profile | Commands | Code Blocks | Tests | Evidence |
|---|---|---|---|---|---|---|---:|---|---|---|---|---|
""" + rows,
        encoding="utf-8",
    )

    findings = validate_artifact_set([master, phase], [{"blocks": []}])

    assert "phase_subfeature_layout_required:backend:files=9" in findings
