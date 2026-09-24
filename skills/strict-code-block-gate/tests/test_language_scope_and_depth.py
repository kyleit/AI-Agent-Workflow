"""Prove language scope and declared depth are decided from declarations, not prose.

The two narrowing cases here matter most. A validator that stops demanding Go
toolchain evidence from a real Go project would be a worse defect than the one
being repaired, so every relaxation is paired with a positive case.
"""

import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FENCE = "`" * 3


def _module(name: str):
    path = SCRIPTS / f"{name}.py"
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _document(depth: str, blocks: list[dict], *, branch: str = "A") -> str:
    lines = [
        "---",
        f"blueprint_depth: {depth}",
        f"source_verification_branch: {branch}",
        "project_initialization: false",
        "---",
        "",
        "# Fixture Blueprint",
        "",
        "## Data Flow And Sequence Diagram",
        "",
        "author to gate to findings, one real run end-to-end",
        "",
        "## File-By-File Change Matrix",
        "",
        "| File | Operation | Projected Lines | Code Block IDs |",
        "| --- | --- | --- | --- |",
    ]
    for block in blocks:
        lines.append(f"| `{block['file']}` | {block['operation']} | 20 | `{block['id']}` |")
    lines.append("")
    for block in blocks:
        lines.append("Verified from: real fixture file on disk.")
        lines.append("")
        lines.append("### Block")
        lines.append("")
        for key, value in block.items():
            if key == "body":
                continue
            lines.append(f"{key}: {value}")
        lines.append("implementation_ready: true")
        lines.append(f"{FENCE}{block.get('language', 'python')}")
        lines.append(block.get("body", "def placeholder_free() -> int:\n    return 1"))
        lines.append(FENCE)
        lines.append("")
    lines += ["## NO-GO Conditions", "", "Any blocking finding."]
    return "\n".join(lines) + "\n"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


PY_BLOCK = {
    "id": "FX-PY", "language": "python", "file": "pkg/module.py", "operation": "create",
    "symbol": "run", "full_file": "true", "block_scope": "full-file",
    "body": "def run() -> int:\n    return 1",
}
GO_BLOCK = {
    "id": "FX-GO", "language": "go", "file": "cmd/app/main.go", "operation": "create",
    "symbol": "main", "full_file": "true", "block_scope": "full-file",
    "body": "package main\n\nfunc main() {\n}",
}
GO_MANIFEST_BLOCK = {
    "id": "FX-MOD", "language": "go", "file": "go.mod", "operation": "create",
    "symbol": "module", "full_file": "true", "block_scope": "full-file",
    "body": "module example.com/app\n\ngo 1.22",
}


def _findings(tmp_path: Path, depth: str, blocks: list[dict], *, branch: str = "A",
              extra: list[tuple[str, str, list[dict]]] | None = None) -> list[str]:
    spike = _module("validate_spike_verified_blueprint")
    discover = _module("discover_code_blocks").discover
    master = _write(tmp_path, "docs/features/fx/blueprints/master.md",
                    _document(depth, blocks, branch=branch))
    all_blocks = list(discover(master)["blocks"])
    for name, phase_depth, phase_blocks in extra or []:
        phase = _write(tmp_path, f"docs/features/fx/blueprints/fam/{name}",
                       _document(phase_depth, phase_blocks, branch=branch))
        all_blocks.extend(discover(phase)["blocks"])
    scratch = tmp_path / ".agents" / "scratch" / "FX"
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "spike-run.log").write_text("no commands recorded\n", encoding="utf-8")
    result = spike.validate(master, all_blocks, project_root=tmp_path, workflow_id="FX")
    return result["blocking_findings"]


def test_block_records_its_source_artifact(tmp_path: Path) -> None:
    discover = _module("discover_code_blocks").discover
    master = _write(tmp_path, "m.md", _document("FULL", [PY_BLOCK]))
    blocks = [b for b in discover(master)["blocks"] if b["implementation_ready"]]
    assert blocks
    assert all(b["artifact"] == str(master) for b in blocks)


def test_no_go_heading_does_not_imply_go_scope(tmp_path: Path) -> None:
    assert "NO-GO" in _document("FULL", [PY_BLOCK], branch="B")
    findings = _findings(tmp_path, "FULL", [PY_BLOCK], branch="B")
    assert not [f for f in findings if "spike_verified_exact_command_missing" in f]


def test_real_go_file_still_demands_toolchain(tmp_path: Path) -> None:
    findings = _findings(tmp_path, "FULL", [GO_BLOCK], branch="B")
    demanded = {
        f.split(":", 1)[1]
        for f in findings
        if f.startswith("spike_verified_exact_command_missing")
    }
    assert demanded == {"gofmt -l .", "go build ./...", "go vet ./...", "go test ./... -v"}


def test_go_manifest_implies_go_scope(tmp_path: Path) -> None:
    findings = _findings(tmp_path, "FULL", [GO_MANIFEST_BLOCK], branch="B")
    assert [f for f in findings if f.startswith("spike_verified_exact_command_missing")]


def test_phase_declaring_contract_is_rejected(tmp_path: Path) -> None:
    findings = _findings(tmp_path, "CONTRACT", [PY_BLOCK],
                         extra=[("phase-01.md", "CONTRACT", [dict(PY_BLOCK, id="FX-P1")])])
    offenders = [f for f in findings if f.startswith("phase_depth_contract_not_permitted")]
    assert offenders == ["phase_depth_contract_not_permitted:phase-01.md"]


def test_full_phase_completeness_is_enforced(tmp_path: Path) -> None:
    partial = dict(PY_BLOCK, id="FX-PART", file="pkg/partial.py",
                   full_file="false", block_scope="fragment")
    findings = _findings(tmp_path, "CONTRACT", [PY_BLOCK],
                         extra=[("phase-01.md", "FULL", [partial])])
    assert any(
        f.startswith("full_depth_non_full_file_blocks") and "FX-PART" in f
        for f in findings
    )


def test_contract_master_still_enforces_full_phases(tmp_path: Path) -> None:
    good = dict(PY_BLOCK, id="FX-OK", file="pkg/ok.py")
    findings = _findings(tmp_path, "CONTRACT", [PY_BLOCK],
                         extra=[("phase-01.md", "FULL", [good])])
    assert not [f for f in findings if f.startswith("phase_depth_contract_not_permitted")]
    assert not [f for f in findings if f.startswith("full_depth_non_full_file_blocks")]


def test_shipped_contract_satisfies_architecture_validator(tmp_path: Path) -> None:
    boundaries = _module("validate_architecture_boundaries")
    shipped = SCRIPTS.parents[2] / "contracts" / "engineering-quality-gates.yaml"
    assert shipped.is_file(), "the framework must ship the architecture contract"

    provisioned = tmp_path / ".agents" / "contracts"
    provisioned.mkdir(parents=True)
    destination = provisioned / "engineering-quality-gates.yaml"
    destination.write_text(shipped.read_text(encoding="utf-8"), encoding="utf-8")
    before = destination.read_bytes()

    results = boundaries.validate(
        tmp_path, [{"id": "B1", "implementation_ready": True, "file": "pkg/module.py"}]
    )
    assert results == [{
        "id": "B1",
        "status": "PASS",
        "contract": ".agents/contracts/engineering-quality-gates.yaml",
    }]
    assert destination.read_bytes() == before

    missing = boundaries.validate(tmp_path / "elsewhere", [])
    assert missing == [{"status": "BLOCKED", "finding": "missing architecture contract"}]
