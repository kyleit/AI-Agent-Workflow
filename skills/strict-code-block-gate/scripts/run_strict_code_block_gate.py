#!/usr/bin/env python3
"""Run the strict polyglot CODE_BLOCK_GATE without executing project tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from aggregate_gate_results import aggregate  # noqa: E402
from discover_code_blocks import discover  # noqa: E402
from materialize_validation_scope import materialize  # noqa: E402
from resolve_language_profile import load_registry, resolve  # noqa: E402
from validate_architecture_boundaries import validate  # noqa: E402
from validate_artifact_set_code_blocks import validate_artifact_set  # noqa: E402
from validate_spike_verified_blueprint import validate as validate_spike_verified  # noqa: E402


DEFAULT_REGISTRY = "skills/strict-code-block-gate/config/language-profiles.yaml"
_BINARY_ASSET_SUFFIXES = {".woff2", ".woff", ".ttf", ".otf", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".svg"}


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


def discover_phase_paths(blueprint_abs: Path) -> list[Path]:
    """Discover all Markdown phase artifacts below the master blueprint."""
    return sorted(
        path.resolve()
        for path in blueprint_abs.parent.rglob("*.md")
        if path.resolve() != blueprint_abs
    )


def validate_real_file_alignment(root: Path, blocks: list[dict]) -> list[str]:
    """Compare declared full-file blocks with already materialized workspace files."""
    findings: list[str] = []
    for block in blocks:
        if not block.get("implementation_ready") or not block.get("full_file"):
            continue
        relative = str(block.get("file", "")).replace("\\", "/").strip()
        if not relative or re.match(r"^(?:[A-Za-z]:|/|\\\\)", relative):
            findings.append(f"code_block_absolute_or_empty_target:{block.get('id', '')}:{relative}")
            continue
        target = (root / Path(relative)).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            findings.append(f"code_block_target_outside_root:{block.get('id', '')}:{relative}")
            continue
        if not target.is_file() or target.suffix.lower() in _BINARY_ASSET_SUFFIXES:
            continue
        try:
            actual = target.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()
            declared = str(block.get("code", "")).replace("\r\n", "\n").rstrip()
        except (OSError, UnicodeError) as exc:
            findings.append(f"code_block_workspace_read_failed:{block.get('id', '')}:{type(exc).__name__}")
            continue
        if actual != declared:
            findings.append(f"code_block_workspace_mismatch:{block.get('id', '')}:{relative}")
    return findings


def validate_binary_asset_alignment(root: Path, blocks: list[dict]) -> list[str]:
    """Verify that declared binary assets are real workspace inputs.

    Markdown can describe a binary asset, but it cannot carry the bytes. The
    target workspace must therefore contain the actual asset before a strict
    gate can pass. This catches text placeholders masquerading as local fonts.
    """
    findings: list[str] = []
    signatures = {
        ".woff2": (b"wOF2",),
        ".woff": (b"wOFF",),
        ".ttf": (b"\x00\x01\x00\x00", b"true", b"ttcf"),
        ".otf": (b"OTTO", b"ttcf"),
    }
    for block in blocks:
        if not block.get("implementation_ready"):
            continue
        relative = str(block.get("file", "")).replace("\\", "/").strip()
        suffix = Path(relative).suffix.lower()
        if suffix not in _BINARY_ASSET_SUFFIXES:
            continue
        if not relative or re.match(r"^(?:[A-Za-z]:|/|\\\\)", relative):
            continue
        target = (root / Path(relative)).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            continue
        if not target.is_file():
            findings.append(f"binary_asset_workspace_missing:{block.get('id', '')}:{relative}")
            continue
        data = target.read_bytes()
        if not data:
            findings.append(f"binary_asset_workspace_empty:{block.get('id', '')}:{relative}")
            continue
        if suffix in signatures and not any(data.startswith(magic) for magic in signatures[suffix]):
            findings.append(f"binary_font_invalid_signature:{block.get('id', '')}:{relative}")
        if b"placeholder" in data.lower() or b"sample only" in data.lower() or b"not implemented" in data.lower():
            findings.append(f"binary_asset_workspace_placeholder:{block.get('id', '')}:{relative}")
        if suffix == ".svg" and b"<svg" not in data[:4096].lower():
            findings.append(f"binary_svg_invalid_document:{block.get('id', '')}:{relative}")
    return findings


def run(
    root: Path,
    blueprint: Path,
    workflow_id: str,
    registry_path: Path,
    phase_blueprints: list[Path] | None = None,
) -> dict:
    blueprint_abs = (root / blueprint).resolve() if not blueprint.is_absolute() else blueprint.resolve()
    location_findings = validate_blueprint_location(root, blueprint_abs)
    before_hash = sha256_file(blueprint_abs) if blueprint_abs.is_file() else "0" * 64
    before_text = blueprint_abs.read_text(encoding="utf-8") if blueprint_abs.is_file() else ""
    if not _has_data_flow_sequence_heading(before_text):
        location_findings.append("master_data_flow_and_sequence_diagram_missing")
    artifact_paths = [blueprint_abs]
    # Phase artifacts are often named by their phase id (for example
    # ``P01_backend_core.md``), not with the word ``blueprint`` in the
    # filename.  The parent directory is already the canonical blueprint
    # scope, so discover every Markdown artifact below it and let the
    # artifact-set validator reject unrelated or malformed documents.
    discovered_phase_paths = discover_phase_paths(blueprint_abs)
    for phase in phase_blueprints or []:
        phase_abs = (root / phase).resolve() if not phase.is_absolute() else phase.resolve()
        if phase_abs not in artifact_paths:
            artifact_paths.append(phase_abs)
    for phase_abs in discovered_phase_paths:
        if phase_abs not in artifact_paths:
            artifact_paths.append(phase_abs)
    discoveries = [discover(path) for path in artifact_paths]
    discovery = discoveries[0]
    registry = load_registry(registry_path)
    profile_results = []
    all_blocks = []
    for item in discoveries:
        all_blocks.extend(item["blocks"])
        for block in item["blocks"]:
            if not block.get("implementation_ready"):
                profile_results.append({"id": block["id"], "status": "NOT_APPLICABLE"})
                continue
            resolved = resolve(registry, block.get("language", ""), block.get("file", ""))
            profile_results.append({"id": block["id"], **resolved})
    combined_discovery = {"blocks": all_blocks}
    materialized = materialize(combined_discovery, root, workflow_id)
    architecture_results = validate(root, all_blocks)
    completeness_findings = validate_artifact_set(artifact_paths, discoveries)
    spike_verification = validate_spike_verified(
        blueprint_abs,
        all_blocks,
        project_root=root,
        workflow_id=workflow_id,
    )
    after_hash = sha256_file(blueprint_abs) if blueprint_abs.is_file() else "0" * 64
    after_text = blueprint_abs.read_text(encoding="utf-8") if blueprint_abs.is_file() else ""
    integrity_findings: list[str] = []
    if before_hash != after_hash or before_text != after_text:
        integrity_findings.append("blueprint_content_changed")
    if not _has_data_flow_sequence_heading(after_text):
        integrity_findings.append("blueprint_data_flow_section_changed_or_missing")
    payload = {
        "schema_version": "1.0.0",
        "gate": "CODE_BLOCK_GATE",
        "authority": "strict-code-block-gate",
        "workflow_id": workflow_id,
        "blueprint_path": str(blueprint),
        "blueprint_full_sha256": sha256_file(blueprint_abs),
        "artifact_set": [str(path) for path in artifact_paths],
        "per_code_block": [{k: v for k, v in block.items() if k != "code"} for block in all_blocks],
        "profile_results": profile_results,
        "materialized_scope": materialized,
        "architecture_results": architecture_results,
        "spike_verification": spike_verification,
        "blocking_findings": [
            finding
            for item in discoveries
            for finding in item.get("findings", [])
        ]
        + location_findings
        + completeness_findings
        + spike_verification.get("blocking_findings", [])
        + integrity_findings
        + validate_real_file_alignment(root, all_blocks)
        + validate_binary_asset_alignment(root, all_blocks),
        "test_status": "NOT_RUN",
    }
    return aggregate(payload)


def validate_blueprint_location(root: Path, blueprint: Path) -> list[str]:
    """Keep Blueprint inputs inside the canonical relative artifact folders."""
    try:
        relative = blueprint.relative_to(root).as_posix()
    except ValueError:
        return ["blueprint_outside_root"]
    if re.match(r"^docs/features/[^/]+/blueprints/[^/]+\.md$", relative, re.IGNORECASE):
        return []
    if re.match(r"^docs/blueprints/[^/]+\.md$", relative, re.IGNORECASE):
        return []
    return [f"blueprint_location_invalid:{relative}"]


def _has_data_flow_sequence_heading(text: str) -> bool:
    return bool(
        re.search(
            r"^#{1,6}\s+.*(?:data\s+flow.*sequence\s+diagram|sequence.*data\s+flow.*diagram)",
            text,
            re.IGNORECASE | re.MULTILINE,
        )
    )


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
    parser.add_argument("--phase-blueprint", action="append", default=[])
    parser.add_argument("--output")
    parser.add_argument("--no-execute", action="store_true", help="Accepted for explicit audit clarity; project tests are never executed.")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    blueprint = Path(args.blueprint)
    registry_path = resolve_registry_path(root, args.registry)
    try:
        result = run(
            root,
            blueprint,
            args.workflow_id,
            registry_path,
            [Path(item) for item in args.phase_blueprint],
        )
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
