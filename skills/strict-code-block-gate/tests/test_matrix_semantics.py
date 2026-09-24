"""Prove matrix semantics and surface gating read declarations, not prose.

Three changes in this batch make the gate accept something it used to reject. Each
has a positive counterpart here that must still fail, because a validator that stops
rejecting genuine omissions would be a worse defect than the one being repaired.
"""

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"

HEADERS = (
    "| File | Operation | Projected Lines | Code Block IDs | Owner | Imports "
    "| Exports | Exact Signatures | Commands | Tests | Evidence |"
)
RULE = "|---|---|---:|---|---|---|---|---|---|---|---|"


def _module(name: str):
    path = SCRIPTS / f"{name}.py"
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(file: str, blocks: str, *, operation: str = "create", lines: int = 20) -> str:
    return (
        f"| `{file}` | {operation} | {lines} | {blocks} | IMPLEMENTER | `os` | `run` "
        f"| `run() -> int` | `pytest -q` | `t1` | `receipt.json` |"
    )


def _document(rows: list[str], *, initialization: str = "false", extra: str = "") -> str:
    return "\n".join(
        [
            "---",
            "blueprint_depth: FULL",
            "source_verification_branch: A",
            f"project_initialization: {initialization}",
            "---",
            "",
            "# Fixture Master Blueprint",
            "",
            "## Data Flow And Sequence Diagram",
            "",
            "author to gate to findings, one real run end-to-end",
            "",
            "## File-By-File Change Matrix",
            "",
            HEADERS,
            RULE,
            *rows,
            "",
            extra,
            "",
            "## NO-GO Conditions",
            "",
            "Any blocking finding.",
        ]
    ) + "\n"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _entries(tmp_path: Path, document: str):
    coverage = _module("validate_artifact_set_code_blocks")
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md", document)
    return coverage.extract_file_matrix_entries(master)


# ---------------------------------------------------------------- parsing layer


def test_escaped_pipe_does_not_shift_columns() -> None:
    cells = _module("matrix_cells").cells
    row = (
        r"| `pkg/m.py` | modify | 20 | `B1` | OWNER | `os` | `run` "
        r"| `run() -> Path \| None` | `pytest -q` | `t1` | `receipt.json` |"
    )
    values = cells(row)
    assert len(values) == 11
    assert values[7] == "run() -> Path | None"
    assert values[8] == "pytest -q"
    assert values[10] == "receipt.json"


def test_slash_bearing_marker_yields_no_identifiers() -> None:
    ids = _module("matrix_cells").ids
    assert ids("N/A") == []
    assert ids("n / a") == []
    assert ids("none") == []
    assert ids("-") == []


def test_not_applicable_reason_is_never_tokenized() -> None:
    cells_module = _module("matrix_cells")
    value = "NOT_APPLICABLE — nguồn khác, không phải mã"
    assert cells_module.cell_is_not_applicable(value)
    assert cells_module.ids(value) == []


def test_real_identifier_list_is_unchanged() -> None:
    ids = _module("matrix_cells").ids
    assert ids("`B1`, `B2`") == ["B1", "B2"]
    assert ids("FIX420BB-B03") == ["FIX420BB-B03"]


def test_finding_paths_are_repository_relative(tmp_path: Path) -> None:
    display_path = _module("matrix_cells").display_path
    absolute = tmp_path / "docs" / "features" / "fx" / "blueprints" / "master.md"
    rendered = display_path(absolute)
    assert rendered == "docs/features/fx/blueprints/master.md"
    assert not rendered.startswith("/")

    _, findings = _entries(tmp_path, _document([]))
    for finding in findings:
        assert str(tmp_path) not in finding


# ------------------------------------------------------------ coverage semantics


def test_not_applicable_row_is_honoured(tmp_path: Path) -> None:
    coverage = _module("validate_artifact_set_code_blocks")
    document = _document([
        _row("docs/features/fx/reports/evidence.md",
             "NOT_APPLICABLE — evidence log, not source code"),
    ])
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md", document)
    findings = coverage.validate_artifact_set([master], [{"blocks": []}])
    assert not [f for f in findings if f.startswith("file_matrix_row_missing_code_block")]
    assert not [f for f in findings if f.startswith("file_matrix_unknown_code_block")]


def test_contradictory_coverage_row_is_rejected(tmp_path: Path) -> None:
    """A row claiming no source code applies, while a real block targets that file.

    The contradiction is decided from the discovered blocks, not by parsing the text
    after the marker. Guessing whether that text is an identifier or a free-text
    reason is exactly the inference this batch removes.
    """
    coverage = _module("validate_artifact_set_code_blocks")
    document = _document([_row("pkg/m.py", "NOT_APPLICABLE — handled elsewhere")])
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md", document)
    discovery = {"blocks": [{
        "id": "B1", "implementation_ready": True, "file": "pkg/m.py",
        "operation": "create", "full_file": True, "block_scope": "full-file",
        "language": "python", "code": "def run() -> int:\n    return 1\n",
    }]}
    findings = coverage.validate_artifact_set([master], [discovery])
    assert any(f.startswith("file_matrix_contradictory_coverage") for f in findings)


def test_row_column_count_mismatch_is_named(tmp_path: Path) -> None:
    coverage = _module("validate_artifact_set_code_blocks")
    wide = _row("pkg/m.py", "`B1`")[:-1] + " extra | more |"
    document = _document([wide])
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md", document)
    findings = coverage.validate_artifact_set([master], [{"blocks": []}])
    assert any(f.startswith("file_matrix_row_column_count_mismatch") for f in findings)


def test_not_applicable_row_exempt_from_strict_fields(tmp_path: Path) -> None:
    coverage = _module("validate_artifact_set_code_blocks")
    bare = (
        "| `docs/features/fx/reports/evidence.md` | create | 10 "
        "| NOT_APPLICABLE — retained evidence | | | | | | | |"
    )
    entries, _ = _entries(tmp_path, _document([bare]))
    assert entries and entries[0]["not_applicable"] == "true"
    assert coverage._strict_matrix_findings(entries) == []


def test_ordinary_row_still_requires_a_block(tmp_path: Path) -> None:
    coverage = _module("validate_artifact_set_code_blocks")
    document = _document([_row("pkg/m.py", "")])
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md", document)
    findings = coverage.validate_artifact_set([master], [{"blocks": []}])
    assert any(f.startswith("file_matrix_row_missing_code_block") for f in findings)


def test_moved_functions_are_still_importable_here() -> None:
    coverage = _module("validate_artifact_set_code_blocks")
    assert callable(coverage.validate_project_initialization_surface)
    assert callable(coverage.validate_greenfield_completeness_matrices)


# ------------------------------------------------------------------ surface gate


def _surface_document(initialization: str) -> str:
    prose = (
        "The interface contract table has a column named Input, the query uses a "
        "SELECT keyword, and the digest is a hash produced beside the web router."
    )
    return _document([_row("pkg/service.py", "`B1`")],
                     initialization=initialization, extra=prose)


def test_surface_obligations_skipped_when_not_an_initialization(tmp_path: Path) -> None:
    surface = _module("validate_project_surface")
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md",
                    _surface_document("false"))
    entries = [{"file": "pkg/service.py"}]
    assert surface.validate_project_initialization_surface([master], entries, {}) == []
    assert surface.validate_greenfield_completeness_matrices([master]) == []


def test_declared_initialization_still_demands_obligations(tmp_path: Path) -> None:
    surface = _module("validate_project_surface")
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md",
                    _surface_document("true"))
    entries = [{"file": "pkg/service.py"}]
    findings = surface.validate_project_initialization_surface([master], entries, {})
    assert [f for f in findings if f.startswith("project_init_required_surface_missing")]


def test_declared_initialization_still_requires_matrices(tmp_path: Path) -> None:
    surface = _module("validate_project_surface")
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md",
                    _surface_document("true"))
    findings = surface.validate_greenfield_completeness_matrices([master])
    assert [f for f in findings if f.startswith("greenfield_required_matrix_missing")]


def test_declaration_is_read_from_front_matter_not_prose(tmp_path: Path) -> None:
    surface = _module("validate_project_surface")
    discussing = _document(
        [_row("pkg/service.py", "`B1`")],
        initialization="false",
        extra="This document explains the project_initialization: true declaration.",
    )
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md", discussing)
    assert surface.initialization_declared([master]) is False
    assert surface.validate_greenfield_completeness_matrices([master]) == []


# --------------------------------------------------------------- family counting


def _family(tmp_path: Path, rows_per_phase: int, phases: int) -> list[Path]:
    master = _write(
        tmp_path,
        "docs/features/fx/blueprints/master.md",
        _document([_row("pkg/root.py", "`B0`")], extra="Master Blueprint index."),
    )
    paths = [master]
    for index in range(phases):
        rows = [_row(f"pkg/m{index}_{n}.py", f"`B{index}{n}`") for n in range(rows_per_phase)]
        relative = f"docs/features/fx/blueprints/fam/phase-{index:02d}.md"
        paths.append(_write(tmp_path, relative, _document(rows)))
    return paths


def _collect(coverage, paths: list[Path]) -> list[dict]:
    entries: list[dict] = []
    for path in paths:
        found, _ = coverage.extract_file_matrix_entries(path)
        entries.extend(found)
    return entries


def test_family_counts_come_from_extracted_rows(tmp_path: Path) -> None:
    coverage = _module("validate_artifact_set_code_blocks")
    paths = _family(tmp_path, rows_per_phase=2, phases=2)
    verbs = "\n".join(
        f"| `T{n}` | Own it | Add one import line | none | x | y | z | do it | ok | log | revert |"
        for n in range(9)
    )
    paths[1].write_text(paths[1].read_text(encoding="utf-8") + "\n" + verbs + "\n",
                        encoding="utf-8")
    findings = coverage._hierarchy_findings(paths, _collect(coverage, paths))
    assert not [f for f in findings if f.startswith("phase_subfeature_layout_required")]


def test_genuine_large_family_still_requires_subfeatures(tmp_path: Path) -> None:
    coverage = _module("validate_artifact_set_code_blocks")
    paths = _family(tmp_path, rows_per_phase=5, phases=2)
    findings = coverage._hierarchy_findings(paths, _collect(coverage, paths))
    assert any(f.startswith("phase_subfeature_layout_required") for f in findings)
