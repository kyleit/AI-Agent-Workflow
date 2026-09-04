from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from workflow_runtime.application.command_contract import (
    CommandResult,
    NextAction,
    emit_result,
)


def _blueprint_phases(path: Path) -> list[str]:
    phases = [
        line[3:].strip()
        for line in path.read_text(encoding="utf-8-sig").splitlines()
        if line.startswith("## ") and line[3:].strip()
    ]
    return phases or ["blueprint"]


def _approved_blueprint_matches(path: Path) -> bool:
    from workflow_runtime.infrastructure.session.session_io import load_session

    session = load_session() or {}
    raw_blueprint = session.get("blueprint")
    blueprint = raw_blueprint if isinstance(raw_blueprint, dict) else {}
    approved_path = str(blueprint.get("path", "") or "")
    try:
        return bool(blueprint.get("approved")) and Path(approved_path).resolve() == path.resolve()
    except OSError:
        return False


def _implementation_entry_receipt(
    blueprint_path: Path,
    work_item_id: str,
) -> tuple[dict[str, object], Path]:
    """Persist the machine-readable handoff consumed by implementation skills."""
    from workflow_runtime.infrastructure.session.session_io import load_session

    session = load_session() or {}
    blueprint_text = blueprint_path.read_text(encoding="utf-8-sig")
    frontmatter = blueprint_text.split("---", 2)[1] if blueprint_text.startswith("---") else ""
    metadata = {
        key.strip(): value.strip()
        for key, value in re.findall(r"^([a-z_]+):\s*(.+)$", frontmatter, re.MULTILINE)
    }
    workflow_id = str(session.get("workflow_id") or work_item_id)
    feature_id = str(metadata.get("feature_id") or work_item_id)
    blueprint_hash = hashlib.sha256(blueprint_path.read_bytes()).hexdigest()
    gate_path = Path("docs") / "aiwf-runs" / work_item_id / "05-blueprint" / "code-block-gate.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8")) if gate_path.is_file() else {}
    allowed_files = re.findall(r"^\|\s*`([^`\r\n]+)`\s*\|", blueprint_text, re.MULTILINE)
    receipt: dict[str, object] = {
        "workflow_id": workflow_id,
        "feature_id": feature_id,
        "blueprint_id": str(metadata.get("phase_id") or feature_id),
        "blueprint_version": "1.0.0",
        "blueprint_full_sha256": blueprint_hash,
        "code_block_gate_id": str(gate_path).replace("\\", "/"),
        "code_block_gate_decision": str(gate.get("decision") or "BLOCKED"),
        "blueprint_approval_id": f"BLUEPRINT-APPROVAL-{work_item_id}",
        "implementation_approval_id": f"IMPLEMENTATION-APPROVAL-{work_item_id}",
        "implementation_phase": "phase-00-command-envelope",
        "allowed_files": allowed_files,
        "protected_files": [],
        "main_writer": "Main Writer",
        "collaboration_mode": "MODE_B_MULTI_AGENT_SINGLE_WRITER",
        "source_write_allowed": str(gate.get("decision") or "").upper() == "PASS",
        "created_at": datetime.now().astimezone().isoformat(),
        "hash_algorithm": "SHA-256",
    }
    content = json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    receipt["content_hash"] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    receipt_path = Path("docs") / "aiwf-runs" / work_item_id / "06-implementation" / "implementation-entry-receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt, receipt_path


def do_implement_action(args: Any) -> int:
    blueprint_value = str(getattr(args, "blueprint", "") or "").strip()
    dry_run = bool(getattr(args, "dry_run", False))
    if not blueprint_value:
        return emit_result(CommandResult(
            command="implement",
            status="invalid_input",
            summary="A blueprint path is required.",
            blocking_findings=("blueprint_missing",),
            next_action=NextAction(command="implement --blueprint <path>", required=True),
        ), sys.stdout)

    blueprint_path = Path(blueprint_value)
    if not blueprint_path.is_file():
        return emit_result(CommandResult(
            command="implement",
            status="blocked",
            summary="The requested blueprint does not exist.",
            data={"blueprint": blueprint_value, "dry_run": dry_run},
            blocking_findings=("blueprint_not_found",),
            next_action=NextAction(command="blueprint --path <path> --approve", required=True),
        ), sys.stdout)

    phases = _blueprint_phases(blueprint_path)
    approved = _approved_blueprint_matches(blueprint_path)
    from workflow_runtime.infrastructure.session.session_io import load_session

    session = load_session() or {}
    raw_work_item = session.get("work_item")
    work_item = raw_work_item if isinstance(raw_work_item, dict) else {}
    work_item_id = str(work_item.get("id") or session.get("active_workflow") or "FEAT-060")
    findings: list[str] = []
    lifecycle_inspection = None
    try:
        from workflow_runtime.application.workflow.blueprint_lifecycle import BlueprintLifecycleService
        lifecycle_inspection = BlueprintLifecycleService().inspect(blueprint_path, work_item_id)
        if lifecycle_inspection.stale:
            findings.extend(lifecycle_inspection.reasons)
    except (OSError, ValueError) as exc:
        findings.append(str(exc))
    if not approved:
        findings.append("blueprint_not_approved_for_path")
    if dry_run:
        findings.append("dry_run_only")

    receipt_path: Path | None = None
    if approved and not dry_run:
        receipt, receipt_path = _implementation_entry_receipt(blueprint_path, work_item_id)
        if str(receipt.get("code_block_gate_decision", "")).upper() != "PASS":
            findings.append("code_block_gate_not_pass")

    status = "blocked" if findings else "success"
    summary = (
        "Implementation entry is ready for the approved blueprint."
        if not findings
        else "Implementation entry is blocked by the reported gate findings."
    )
    next_action = NextAction(
        skill="blueprint-to-implementation" if not findings else None,
        command="implement --blueprint <path>" if not findings else (
            "blueprint --path <fresh-blueprint> --approve"
            if lifecycle_inspection is not None and lifecycle_inspection.stale
            else "blueprint --path <path> --approve"
        ),
        required=bool(findings),
    )
    return emit_result(CommandResult(
        command="implement",
        status=status,
        summary=summary,
        data={
            "blueprint": str(blueprint_path),
            "dry_run": dry_run,
            "approved": approved,
            "implementation_entry": "ready" if not findings else "blocked",
            "phases": phases,
            "receipt": str(receipt_path) if receipt_path else None,
            "lifecycle": lifecycle_inspection.payload() if lifecycle_inspection is not None else None,
        },
        blocking_findings=tuple(findings),
        artifacts=(str(receipt_path),) if receipt_path else (),
        side_effects=(str(receipt_path),) if receipt_path else (),
        next_action=next_action,
    ), sys.stdout)


def do_project_version_cached(args: argparse.Namespace) -> None:
    """Read project version from cached context.json only — never scans manifests."""
    from workflow_runtime.shared.version_detector import (
        detect_project_version_cached)
    subaction = str(getattr(args, 'action', None) or getattr(args, 'subaction', None))
    if subaction == "version":
        info_dict = detect_project_version_cached()
        print(json.dumps(info_dict, indent=2))
        if str(info_dict.get("version", "0.0.0")) == "0.0.0":
            sys.exit(1)
    else:
        print(f"Unknown project subaction: {subaction}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "do_implement_action",
    "do_project_version_cached",
]
