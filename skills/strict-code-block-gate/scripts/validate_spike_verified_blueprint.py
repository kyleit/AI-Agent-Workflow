"""Validate the evidence contract for Spike-Verified Blueprints.

This validator is structural: it proves that a Blueprint records the required
branch, depth, coverage, and execution evidence. It never substitutes for the
real spike commands, which must be run by the author and retained as evidence.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    result: dict[str, str] = {}
    for line in parts[1].splitlines():
        key, separator, value = line.partition(":")
        if separator:
            result[key.strip().lower().replace("-", "_")] = value.strip().strip("`")
    return result


def _implementation_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in blocks if item.get("implementation_ready")]


def validate(
    blueprint: Path,
    blocks: list[dict[str, Any]],
    project_root: Path | None = None,
    workflow_id: str | None = None,
) -> dict[str, Any]:
    text = blueprint.read_text(encoding="utf-8")
    meta = _frontmatter(text)
    implementation = _implementation_blocks(blocks)
    branch = meta.get("source_verification_branch", "").upper()
    depth = meta.get("blueprint_depth", "").upper()
    findings: list[str] = []

    if branch not in {"A", "B"}:
        findings.append("spike_branch_missing_or_invalid")
    if depth not in {"CONTRACT", "FULL"}:
        findings.append("blueprint_depth_missing_or_invalid")

    has_api_or_schema = bool(re.search(
        r"API|interface|schema|migration|data model|endpoint",
        text,
        re.IGNORECASE,
    ))
    if not implementation and has_api_or_schema:
        findings.append("zero_code_blocks_is_not_vacuous_pass")

    verified_markers = len(re.findall(r"verified\s+from\s*:", text, re.IGNORECASE))
    if branch in {"A", "B"} and implementation and verified_markers != len(implementation):
        findings.append(
            f"verified_marker_mismatch:{verified_markers}!={len(implementation)}"
        )

    if branch == "B":
        required_terms = {
            "scratch": r"\.agents/scratch/[A-Za-z0-9_.-]+/",
            "real_commands": r"exit\s+code|return\s+code|command",
            "adversarial": r"adversarial|invalid|rejected|reject",
            "evidence": r"evidence",
            "complete_extraction": r"complete|full|every|all",
            "memory_prohibition": r"memory",
        }
        for label, pattern in required_terms.items():
            if not re.search(pattern, text, re.IGNORECASE):
                findings.append(f"greenfield_evidence_missing:{label}")

        unit_match = re.search(
            r"public[^\n]*units[^\d]*(\d+)[^\n]*Blueprint[^\d]*(\d+)",
            text,
            re.IGNORECASE,
        )
        if unit_match and unit_match.group(1) != unit_match.group(2):
            findings.append("greenfield_public_unit_count_mismatch")
        if not unit_match:
            findings.append("greenfield_public_unit_counts_missing")

        if project_root is not None and workflow_id:
            scratch_root = project_root / ".agents" / "scratch" / workflow_id
            if not scratch_root.is_dir():
                findings.append(f"greenfield_scratch_missing:{scratch_root.as_posix()}")
            evidence_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in scratch_root.rglob("*")
                if path.is_file() and path.suffix.lower() in {".log", ".md", ".txt", ".json"}
            ) if scratch_root.is_dir() else ""
            is_go_scope = bool(re.search(r"\bgo\b|\.go\b", text, re.IGNORECASE)) or any(
                str(item.get("file", "")).lower().endswith(".go") for item in implementation
            )
            if is_go_scope:
                for command in ("gofmt -l .", "go build ./...", "go vet ./...", "go test ./... -v"):
                    if command not in evidence_text:
                        findings.append(f"spike_verified_exact_command_missing:{command}")
                    elif not re.search(
                        re.escape(command) + r"[\s\S]{0,180}?exit code:?\s*0",
                        evidence_text,
                        re.IGNORECASE,
                    ):
                        findings.append(f"spike_verified_command_result_missing:{command}")

        review_rows = [
            line for line in text.splitlines()
            if "CODE_BLOCK_GATE" in line.upper()
        ]
        review_text = "\n".join(review_rows)
        for required in (
            "B_SPIKE_VERIFIED" if branch == "B" else "A_EXISTING_SOURCE",
            depth,
            str(len(implementation)),
            "verified",
            "no code written from memory",
        ):
            if required and required.lower() not in review_text.lower():
                findings.append(f"spike_verified_internal_review_row_missing:{required}")

    if depth == "FULL":
        if not re.search(r"end[- ]to[- ]end|entrypoint|real run|runs?", text, re.IGNORECASE):
            findings.append("full_depth_end_to_end_evidence_missing")
        incomplete = [
            block.get("id", "")
            for block in implementation
            if block.get("block_scope") != "full-file"
            and Path(str(block.get("file", ""))).suffix.lower() in {".py", ".go", ".ts", ".tsx", ".js", ".sql"}
        ]
        if incomplete:
            findings.append("full_depth_non_full_file_blocks:" + ",".join(incomplete))

    return {
        "branch": branch,
        "blueprint_depth": depth,
        "code_block_count": len(implementation),
        "verified_from_count": verified_markers,
        "public_unit_counts_equal": "greenfield_public_unit_count_mismatch" not in findings,
        "decision": "PASS" if not findings else "BLOCKED",
        "blocking_findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True)
    parser.add_argument("--blocks", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = validate(
        Path(args.blueprint),
        json.loads(Path(args.blocks).read_text(encoding="utf-8")),
    )
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if payload["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
