from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_spike_verified_blueprint.py"
SPEC = importlib.util.spec_from_file_location("spike_policy", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_blueprint(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "blueprint.md"
    path.write_text(
        "---\nsource_verification_branch: B\nblueprint_depth: FULL\n---\n" + body,
        encoding="utf-8",
    )
    return path


def block(file_name: str = "main.py") -> dict[str, object]:
    return {
        "id": "B01",
        "implementation_ready": True,
        "block_scope": "full-file",
        "file": file_name,
    }


def test_zero_blocks_is_blocked_for_api_blueprint(tmp_path: Path) -> None:
    result = MODULE.validate(write_blueprint(tmp_path, "## API interface schema\n"), [])
    assert result["decision"] == "BLOCKED"
    assert "zero_code_blocks_is_not_vacuous_pass" in result["blocking_findings"]


def test_branch_b_requires_adversarial_and_counts(tmp_path: Path) -> None:
    result = MODULE.validate(
        write_blueprint(tmp_path, "## scratch\n## command evidence\n## API\n"),
        [block()],
    )
    assert result["decision"] == "BLOCKED"
    assert "greenfield_evidence_missing:adversarial" in result["blocking_findings"]
    assert "greenfield_public_unit_counts_missing" in result["blocking_findings"]


def test_branch_b_passes_only_with_real_evidence_and_equal_counts(tmp_path: Path) -> None:
    result = MODULE.validate(
        write_blueprint(
            tmp_path,
            """Spike: .agents/scratch/demo/main.py
## Real command evidence
command: python main.py; exit code 0; runs end-to-end from entrypoint
## Adversarial rejection evidence
invalid data rejected; public units 1; Blueprint units 1; full extraction
verified from: .agents/scratch/demo/main.py:1-1
| CODE_BLOCK_GATE | PASS | B_SPIKE_VERIFIED, FULL, 1 verified, no code written from memory |
""",
        ),
        [block()],
    )
    assert result["decision"] == "PASS"
    assert result["public_unit_counts_equal"] is True


def test_full_rejects_partial_python_block(tmp_path: Path) -> None:
    partial = block()
    partial["block_scope"] = "snippet"
    result = MODULE.validate(
        write_blueprint(tmp_path, ".agents/scratch/demo/main.py entrypoint runs"),
        [partial],
    )
    assert result["decision"] == "BLOCKED"
    assert any("full_depth_non_full_file_blocks" in item for item in result["blocking_findings"])
