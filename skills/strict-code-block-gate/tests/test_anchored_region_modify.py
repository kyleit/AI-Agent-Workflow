"""Prove the anchored-region modification contract accepts and rejects correctly.

Every rejection case here corresponds to a way an author could claim a region
without having read the real file. Those cases are the reason ADR-202 permits the
relaxation at all, so they are not optional coverage.
"""

import hashlib
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


def _hash(text: str) -> str:
    normalized = text.replace("\r\n", "\n").rstrip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _target(tmp_path: Path, lines: int = 12) -> Path:
    body = ["def anchored_function() -> int:", "    total = 0"]
    for index in range(lines):
        body.append(f"    total += {index}")
    body.append("    return total")
    target = tmp_path / "pkg" / "module.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(body) + "\n", encoding="utf-8")
    return target


def _blueprint(tmp_path: Path, metadata: dict, code: str) -> Path:
    meta_lines = "\n".join(f"{key}: {value}" for key, value in metadata.items())
    document = "\n".join(
        [
            "---",
            "blueprint_depth: FULL",
            "source_verification_branch: A",
            "project_initialization: false",
            "---",
            "",
            "# Fixture Master Blueprint",
            "",
            "## Data Flow And Sequence Diagram",
            "",
            "author to gate to findings",
            "",
            "## File-By-File Change Matrix",
            "",
            "| File | Operation | Projected Lines | Code Block IDs |",
            "| --- | --- | --- | --- |",
            f"| `pkg/module.py` | {metadata['operation']} | 14 | `{metadata['id']}` |",
            "",
            "Verified from: real fixture file on disk.",
            "",
            "### Block",
            "",
            meta_lines,
            f"{FENCE}python",
            code,
            FENCE,
            "",
            "## NO-GO Conditions",
            "",
            "Any blocking finding.",
        ]
    )
    blueprint = tmp_path / "docs" / "features" / "fixture" / "blueprints" / "master.md"
    blueprint.parent.mkdir(parents=True, exist_ok=True)
    blueprint.write_text(document + "\n", encoding="utf-8")
    return blueprint


def _region_metadata(target_hash: str, **overrides) -> dict:
    metadata = {
        "id": "FIXTURE-R01",
        "language": "python",
        "file": "pkg/module.py",
        "operation": "modify",
        "symbol": "anchored_function",
        "anchor_symbol": "anchored_function",
        "base_sha256": target_hash,
        "implementation_ready": "true",
        "full_file": "false",
        "block_scope": "anchored-region",
    }
    metadata.update(overrides)
    return metadata


def _discover_block(tmp_path: Path, metadata: dict, code: str) -> dict:
    discover = _module("discover_code_blocks").discover
    blueprint = _blueprint(tmp_path, metadata, code)
    blocks = [item for item in discover(blueprint)["blocks"] if item["implementation_ready"]]
    assert len(blocks) == 1
    return blocks[0]


def _alignment_findings(tmp_path: Path, block: dict) -> list[str]:
    runner = _module("run_strict_code_block_gate")
    return runner.validate_real_file_alignment(tmp_path, [block])


REGION_CODE = "def anchored_function() -> int:\n    return 99"


def test_is_region_modify_requires_all_three_conditions() -> None:
    contract = _module("block_contract")
    assert contract.is_region_modify(
        {"operation": "modify", "block_scope": "anchored-region", "full_file": False}
    )
    assert not contract.is_region_modify(
        {"operation": "create", "block_scope": "anchored-region", "full_file": False}
    )
    assert not contract.is_region_modify(
        {"operation": "modify", "block_scope": "full-file", "full_file": False}
    )
    assert not contract.is_region_modify(
        {"operation": "modify", "block_scope": "anchored-region", "full_file": True}
    )


def test_valid_region_block_is_accepted(tmp_path: Path) -> None:
    target = _target(tmp_path)
    metadata = _region_metadata(_hash(target.read_text(encoding="utf-8")))
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    assert block["status"] == "PASS"
    assert block["findings"] == []
    assert _alignment_findings(tmp_path, block) == []


def test_wrong_base_hash_is_rejected(tmp_path: Path) -> None:
    _target(tmp_path)
    metadata = _region_metadata("0" * 64)
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    findings = _alignment_findings(tmp_path, block)
    assert any(item.startswith("anchored_region_base_sha256_mismatch") for item in findings)


def test_missing_base_hash_is_blocked(tmp_path: Path) -> None:
    _target(tmp_path)
    metadata = _region_metadata("")
    metadata.pop("base_sha256")
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    assert block["status"] == "BLOCKED"
    assert "anchored_region_modify_requires_base_sha256" in block["findings"]


def test_missing_anchor_is_blocked(tmp_path: Path) -> None:
    target = _target(tmp_path)
    metadata = _region_metadata(_hash(target.read_text(encoding="utf-8")))
    metadata.pop("anchor_symbol")
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    assert block["status"] == "BLOCKED"
    assert "anchored_region_modify_requires_anchor_symbol" in block["findings"]


def test_region_scope_requires_modify(tmp_path: Path) -> None:
    target = _target(tmp_path)
    metadata = _region_metadata(_hash(target.read_text(encoding="utf-8")), operation="create")
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    assert block["status"] == "BLOCKED"
    assert "anchored_region_requires_modify_operation" in block["findings"]


def test_absent_anchor_is_rejected(tmp_path: Path) -> None:
    target = _target(tmp_path)
    metadata = _region_metadata(
        _hash(target.read_text(encoding="utf-8")),
        anchor_symbol="never_declared_symbol",
    )
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    findings = _alignment_findings(tmp_path, block)
    assert any(item.startswith("anchored_region_anchor_not_found") for item in findings)


def test_missing_target_is_rejected(tmp_path: Path) -> None:
    metadata = _region_metadata("1" * 64)
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    findings = _alignment_findings(tmp_path, block)
    assert any(item.startswith("anchored_region_target_missing") for item in findings)


def test_full_file_mismatch_still_rejected(tmp_path: Path) -> None:
    _target(tmp_path)
    metadata = _region_metadata("")
    metadata.pop("base_sha256")
    metadata.pop("anchor_symbol")
    metadata["full_file"] = "true"
    metadata["block_scope"] = "full-file"
    block = _discover_block(tmp_path, metadata, REGION_CODE)
    findings = _alignment_findings(tmp_path, block)
    assert any(item.startswith("code_block_workspace_mismatch") for item in findings)


def test_region_block_exempt_from_line_ceiling(tmp_path: Path) -> None:
    target = _target(tmp_path, lines=700)
    artifact_set = _module("validate_artifact_set_code_blocks")
    metadata = _region_metadata(_hash(target.read_text(encoding="utf-8")))
    blueprint = _blueprint(tmp_path, metadata, REGION_CODE)
    discover = _module("discover_code_blocks").discover
    discovery = discover(blueprint)
    findings = artifact_set.validate_artifact_set([blueprint], [discovery])
    assert not any("projected_lines_exceed_limit" in item for item in findings)
    assert not any(item.startswith("code_block_not_full_file") for item in findings)
    assert not any(item.startswith("code_block_too_thin") for item in findings)


def test_region_block_exempt_from_full_depth_rule(tmp_path: Path) -> None:
    target = _target(tmp_path)
    spike = _module("validate_spike_verified_blueprint")
    metadata = _region_metadata(_hash(target.read_text(encoding="utf-8")))
    blueprint = _blueprint(tmp_path, metadata, REGION_CODE)
    discover = _module("discover_code_blocks").discover
    blocks = discover(blueprint)["blocks"]
    result = spike.validate(blueprint, blocks, project_root=tmp_path, workflow_id="FIXTURE")
    assert not any(
        item.startswith("full_depth_non_full_file_blocks") for item in result["blocking_findings"]
    )


def test_existing_full_file_behaviour_unchanged(tmp_path: Path) -> None:
    target = _target(tmp_path)
    exact = target.read_text(encoding="utf-8").rstrip()
    metadata = _region_metadata("")
    metadata.pop("base_sha256")
    metadata.pop("anchor_symbol")
    metadata["full_file"] = "true"
    metadata["block_scope"] = "full-file"
    block = _discover_block(tmp_path, metadata, exact)
    assert block["status"] == "PASS"
    assert _alignment_findings(tmp_path, block) == []
