#!/usr/bin/env python3
"""Run the strict polyglot CODE_BLOCK_GATE without executing project tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from aggregate_gate_results import aggregate  # noqa: E402
from discover_code_blocks import discover  # noqa: E402
from materialize_validation_scope import materialize  # noqa: E402
from resolve_language_profile import load_registry, resolve  # noqa: E402
from validate_architecture_boundaries import validate  # noqa: E402


DEFAULT_REGISTRY = "skills/strict-code-block-gate/config/language-profiles.yaml"


def resolve_registry_path(root: Path, configured: str) -> Path:
    """Resolve the registry from the project or the invoked skill mirror.

    Agents commonly invoke this script from an installed ``.agents`` mirror.
    In that layout the project has no top-level ``skills`` directory, so the
    old root-relative default raised ``FileNotFoundError`` before a gate result
    could be returned.  Prefer an explicit project path, then the mirror, and
    finally the config adjacent to this runner.
    """
    requested = Path(configured)
    if requested.is_absolute():
        return requested

    candidates = [root / requested]
    if configured == DEFAULT_REGISTRY:
        candidates.append(root / ".agents" / Path(configured))
        candidates.append(SCRIPT_DIR.parent / "config" / "language-profiles.yaml")

    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return candidates[0].resolve()


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


def blocked_result(root: Path, blueprint: Path, workflow_id: str, finding: str) -> dict:
    """Return a machine-readable blocked result for setup/input failures."""
    blueprint_abs = (root / blueprint).resolve() if not blueprint.is_absolute() else blueprint.resolve()
    blueprint_hash = sha256_file(blueprint_abs) if blueprint_abs.is_file() else "0" * 64
    return {
        "schema_version": "1.0.0",
        "gate": "CODE_BLOCK_GATE",
        "authority": "strict-code-block-gate",
        "workflow_id": workflow_id,
        "blueprint_path": str(blueprint),
        "blueprint_full_sha256": blueprint_hash,
        "decision": "BLOCKED",
        "per_code_block": [],
        "profile_results": [],
        "materialized_scope": [],
        "architecture_results": [],
        "blocking_findings": [finding],
        "test_status": "NOT_RUN",
    }


def exit_code(result: dict) -> int:
    """Make gate decisions usable by both shells and AI command runners."""
    return 0 if result.get("decision") in {"PASS", "NOT_APPLICABLE"} else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry", default=DEFAULT_REGISTRY)
    parser.add_argument("--output")
    parser.add_argument("--no-execute", action="store_true", help="Accepted for explicit audit clarity; project tests are never executed.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    blueprint = Path(args.blueprint)
    registry_path = resolve_registry_path(root, args.registry)
    try:
        result = run(root, blueprint, args.workflow_id, registry_path)
    except (OSError, UnicodeError) as exc:
        result = blocked_result(
            root,
            blueprint,
            args.workflow_id,
            f"GATE_INPUT_ERROR: {type(exc).__name__}: {exc}",
        )
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main())
