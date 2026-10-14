from __future__ import annotations

import importlib
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))


def declaration() -> str:
    return json.dumps({
        "schema_version": "aiwf.contract/1",
        "exports": [{"name": "execute", "signature": "execute(value: str) -> int"}],
        "errors": ["INVALID_INPUT"],
        "invariants": ["Reject invalid input without modifying state"],
        "acceptance": ["CD-01"],
        "verification": ["python -m pytest tests/test_adapter.py"],
    })


def document(path: Path, depth: str = "CONTRACT", body: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nblueprint_depth: {depth}\nsource_verification_branch: A\n---\n"
        "## Data Flow And Sequence Diagram\nInput -> validated contract -> approval\n"
        "## File-By-File Change Matrix\n"
        "| File | Code Block IDs | Contract IDs | Lines |\n"
        "|---|---|---|---|\n"
        "| src/adapter.py | - | C01 | 100 |\n"
        "\nid: C01\nlanguage: json\ntarget_language: python\n"
        "file: src/adapter.py\noperation: create\ncontract_ready: true\n"
        "contract_kind: interface\nblock_scope: contract\nfull_file: false\n"
        f"```json\n{body if body is not None else declaration()}\n```\n",
        encoding="utf-8",
    )


def test_contract_is_discovered_as_contract_not_implementation(tmp_path: Path) -> None:
    path = tmp_path / "blueprint.md"
    document(path)
    block = importlib.import_module("discover_code_blocks").discover(path)["blocks"][0]
    assert block["contract_ready"] is True
    assert block["implementation_ready"] is False
    assert block["status"] == "PASS"


@pytest.mark.parametrize("depth", ["FULL", "", "UNKNOWN"])
def test_contract_cannot_downgrade_full_or_unknown_depth(tmp_path: Path, depth: str) -> None:
    path = tmp_path / "blueprint.md"
    document(path, depth)
    block = importlib.import_module("discover_code_blocks").discover(path)["blocks"][0]
    assert block["status"] == "BLOCKED"


@pytest.mark.parametrize("body", ["{}", "not JSON", declaration().replace("value: str", "value"),
                                  declaration().replace("-> int", "-> Any")])
def test_untyped_or_missing_contract_is_rejected(tmp_path: Path, body: str) -> None:
    path = tmp_path / "blueprint.md"
    document(path, body=body)
    block = importlib.import_module("discover_code_blocks").discover(path)["blocks"][0]
    assert block["status"] == "BLOCKED"


def test_contract_matrix_requires_actual_per_file_declaration(tmp_path: Path) -> None:
    path = tmp_path / "blueprint.md"
    document(path)
    discovery = importlib.import_module("discover_code_blocks").discover(path)
    validator = importlib.import_module("validate_artifact_set_code_blocks")
    assert validator.validate_artifact_set([path], [discovery]) == []
    discovery["blocks"][0]["file"] = "src/other.py"
    assert any("mismatch" in finding for finding in validator.validate_artifact_set([path], [discovery]))


def test_contract_phase_is_allowed_and_full_checks_remain(tmp_path: Path) -> None:
    master = tmp_path / "master.md"
    phase = tmp_path / "family" / "phase.md"
    document(master)
    document(phase)
    block = importlib.import_module("discover_code_blocks").discover(phase)["blocks"][0]
    policy = importlib.import_module("validate_spike_verified_blueprint")
    result = policy.validate(master, [block])
    assert not any("phase_depth_contract_not_permitted" in finding for finding in result["blocking_findings"])
    assert result["decision"] == "PASS"


def test_post_implementation_requires_real_body_and_verification_evidence(tmp_path: Path) -> None:
    path = tmp_path / "blueprint.md"
    document(path)
    block = importlib.import_module("discover_code_blocks").discover(path)["blocks"][0]
    policy = importlib.import_module("contract_blocks")
    findings = policy.verify_implementation(tmp_path, "FEAT-618", [block])
    assert any("target_missing" in finding for finding in findings)
    target = tmp_path / "src" / "adapter.py"
    target.parent.mkdir()
    target.write_text("def execute(value: str) -> int:\n    return len(value)\n", encoding="utf-8")
    findings = policy.verify_implementation(tmp_path, "FEAT-618", [block])
    assert any("verification_evidence_missing" in finding for finding in findings)


def test_duplicate_and_source_na_are_not_valid_contract_coverage(tmp_path: Path) -> None:
    path = tmp_path / "blueprint.md"
    document(path)
    discovery = importlib.import_module("discover_code_blocks").discover(path)
    validator = importlib.import_module("validate_artifact_set_code_blocks")
    discovery["blocks"].append(dict(discovery["blocks"][0]))
    assert "duplicate_code_block_id:C01" in validator.validate_artifact_set([path], [discovery])
    text = path.read_text().replace("| src/adapter.py | - | C01 |", "| src/adapter.py | NOT_APPLICABLE | C01 |")
    path.write_text(text)
    assert any("contradictory" in finding or "source_not_applicable" in finding
               for finding in validator.validate_artifact_set([path], [discovery]))


def test_real_gate_design_pass_requires_real_execution_before_verify(tmp_path: Path) -> None:
    root = tmp_path
    path = root / "docs/features/depth/blueprints/blueprint.md"
    document(path)
    architecture = root / ".agents/contracts/engineering-quality-gates.yaml"
    architecture.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPTS.parents[2] / "contracts/engineering-quality-gates.yaml", architecture)
    runner = importlib.import_module("run_strict_code_block_gate")
    registry = SCRIPTS.parent / "config/language-profiles.yaml"
    result = runner.run(root, path, "FEAT-618", registry)
    assert result["decision"] == "PASS", result["blocking_findings"]
    assert result["deferred_implementation_contracts"] == ["C01"]
    assert result["test_status"] == "NOT_RUN"
    target = root / "src/adapter.py"
    target.parent.mkdir()
    target.write_text("def execute(value: str) -> int:\n    return len(value)\n", encoding="utf-8")
    assert runner.run(root, path, "FEAT-618", registry, post_implementation=True)["decision"] == "BLOCKED"
    test = root / "tests/test_adapter.py"
    test.parent.mkdir()
    test.write_text("from src.adapter import execute\n\ndef test_execute():\n    assert execute('abc') == 3\n")
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_adapter.py", "-q"],
        cwd=root, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    evidence = root / "docs/aiwf-runs/FEAT-618/verification/contract-implementation.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps({
        "work_item_id": "FEAT-618",
        "contracts": {"C01": {
            "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "runs": [{"command": "python -m pytest tests/test_adapter.py", "exit_code": run.returncode,
                      "executed": True, "stdout": run.stdout}],
        }},
    }))
    result = runner.run(root, path, "FEAT-618", registry, post_implementation=True)
    assert result["decision"] == "PASS", result["blocking_findings"]
    target.write_text("def execute(value: int) -> int:\n    return value\n")
    result = runner.run(root, path, "FEAT-618", registry, post_implementation=True)
    assert result["decision"] == "BLOCKED"
    assert any("signature_mismatch" in finding for finding in result["blocking_findings"])
    assert any("stale" in finding for finding in result["blocking_findings"])
