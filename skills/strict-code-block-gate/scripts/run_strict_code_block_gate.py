#!/usr/bin/env python3
"""Run the strict polyglot CODE_BLOCK_GATE without executing project tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from aggregate_gate_results import aggregate
from discover_code_blocks import discover
from materialize_validation_scope import materialize
from resolve_language_profile import load_registry, resolve
from validate_architecture_boundaries import validate


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path, blueprint: Path, workflow_id: str, registry_path: Path) -> dict:
    blueprint_abs = (root / blueprint).resolve() if not blueprint.is_absolute() else blueprint.resolve()
    discovery = discover(blueprint_abs)
    registry = load_registry(registry_path)
    profile_results = []
    for block in discovery["blocks"]:
        if not block.get("implementation_ready"):
            profile_results.append({"id": block["id"], "status": "NOT_APPLICABLE"})
            continue
        resolved = resolve(registry, block.get("language", ""), block.get("file", ""))
        profile_results.append({"id": block["id"], **resolved})
    materialized = materialize(discovery, root, workflow_id)
    architecture_results = validate(root, discovery["blocks"])
    payload = {
        "schema_version": "1.0.0",
        "gate": "CODE_BLOCK_GATE",
        "authority": "strict-code-block-gate",
        "workflow_id": workflow_id,
        "blueprint_path": str(blueprint),
        "blueprint_full_sha256": sha256_file(blueprint_abs),
        "per_code_block": [
            {k: v for k, v in block.items() if k != "code"} for block in discovery["blocks"]
        ],
        "profile_results": profile_results,
        "materialized_scope": materialized,
        "architecture_results": architecture_results,
        "blocking_findings": discovery.get("findings", []),
        "test_status": "NOT_RUN",
    }
    return aggregate(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry", default="skills/strict-code-block-gate/config/language-profiles.yaml")
    parser.add_argument("--output")
    parser.add_argument("--no-execute", action="store_true", help="Accepted for explicit audit clarity; project tests are never executed.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    result = run(root, Path(args.blueprint), args.workflow_id, root / args.registry)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
