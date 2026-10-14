from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import cast
from argparse import Namespace
from workflow_runtime.application.ports.source_capability import IssueRequest, SourceCapabilityPort

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
    from workflow_runtime.infrastructure.session.state_store import AtomicFileStateStore
    text = path.read_text(encoding="utf-8-sig")
    match = re.search(r"^(?:feature_id|issue_id|quick_id|work_item_id):\s*(\S+)", text, re.MULTILINE)
    if not match:
        return False
    store = AtomicFileStateStore(os.environ.get("AIWF_STATE_ROOT", ".agents/state"), match.group(1))
    raw = store.get("approvals").get("blueprint")
    blueprint = cast(dict[str, object], raw) if isinstance(raw, dict) else {}
    return (blueprint.get("approved") is True and blueprint.get("work_item_id") == match.group(1)
            and Path(str(blueprint.get("path", ""))).resolve() == path.resolve()
            and blueprint.get("sha256") == hashlib.sha256(path.read_bytes()).hexdigest())


def _implementation_entry_receipt(blueprint_path: Path, work_item_id: str,
                                  port: SourceCapabilityPort, request: IssueRequest) -> tuple[dict[str, object], Path]:
    from workflow_runtime.infrastructure.session.state_store import AtomicFileStateStore

    root = Path.cwd().resolve()
    blueprint_path.resolve().relative_to(root)
    store = AtomicFileStateStore(os.environ.get("AIWF_STATE_ROOT", ".agents/state"), work_item_id)
    workflow = store.get("workflow")
    workflow.update({"active_workflow": work_item_id, "active_phase": "implementation", "status": "IN_PROGRESS"})
    store.set("workflow", workflow)
    result = port.issue(request)
    if not result.issued:
        raise ValueError(result.reason)
    receipt = dict(result.receipt)
    report = Path("docs") / "aiwf-runs" / work_item_id / "06-implementation" / "implementation-entry-receipt.json"
    try:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ValueError("RECEIPT_PUBLISHED_REPORT_COPY_FAILED:" + result.receipt_path) from exc
    return receipt, report


def _run_legacy_implement_action(action: str) -> int:
    """Keep documented inspection and recovery actions independent of a blueprint."""
    from workflow_runtime.infrastructure.persistence.ledger import ImplementationLedger

    ledger = ImplementationLedger()
    if action == "status":
        data = ledger.load()
        gate = ledger.get_release_gate_status()
        print(json.dumps({
            "status": "ok",
            "current_phase": data.get("current_phase"),
            "phases": ledger.get_phase_summary(),
            "release_allowed": bool(gate.get("release_allowed")),
            "release_block_reason": str(gate.get("release_block_reason", "")),
        }))
        return 0

    if action == "resume":
        from workflow_runtime.application.workflow.phase_controller import PhaseController

        next_phase = PhaseController().resume_next_phase()
        if next_phase is None:
            print(json.dumps({
                "status": "nothing_to_resume",
                "message": "No pending implementation phase found.",
            }))
            return 1
        print(json.dumps({"status": "resumed", "next_phase": next_phase}))
        return 0

    if action == "abort":
        from workflow_runtime.infrastructure.execution.worker_manager import WorkerManager
        from workflow_runtime.infrastructure.persistence.lock_manager import LockManager

        worker_manager = WorkerManager()
        lock_manager = LockManager()
        workers = worker_manager.get_active_workers()
        locks = lock_manager.get_active_locks()
        for worker in workers:
            worker_id = str(worker.get("worker_id", ""))
            if worker_id:
                worker_manager.terminate_orphan(worker_id, force=True)
        for lock in locks:
            task_id = str(lock.get("task_id", ""))
            if task_id:
                lock_manager.release(task_id)
        print(json.dumps({
            "status": "aborted",
            "workers_killed": len(workers),
            "locks_released": len(locks),
        }))
        return 0

    print(json.dumps({
        "status": "blocked",
        "message": "partial-release requires an approved phase confirmation.",
    }))
    return 1


def do_implement_action(args: Namespace) -> int:
    action = str(getattr(args, "action", "") or "").strip()
    if action:
        return _run_legacy_implement_action(action)

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
    text = blueprint_path.read_text(encoding="utf-8-sig")
    match = re.search(r"^(?:feature_id|issue_id|quick_id|work_item_id):\s*(\S+)", text, re.MULTILINE)
    work_item_id = match.group(1) if match else ""
    explicit = str(getattr(args, "work_item", "") or "")
    env_item = os.environ.get("AIWF_WORK_ITEM_ID") or os.environ.get("AIWF_ACTIVE_WORK_ITEM")
    if not work_item_id or (explicit and explicit != work_item_id) or (env_item and env_item != work_item_id):
        return emit_result(CommandResult(command="implement", status="blocked", summary="Implementation context mismatch.",
                                         blocking_findings=("CONTEXT_MISMATCH",)), sys.stdout)
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
    if approved and not findings:
        try:
            import time
            from workflow_runtime.infrastructure.execution.source_capability_adapter import GateSourceCapabilityAdapter
            root = Path.cwd().resolve()
            adapter = GateSourceCapabilityAdapter(root)
            request = adapter.request(blueprint_path.resolve().relative_to(root).as_posix(), work_item_id,
                                      os.environ.get('AIWF_OWNER_ID', 'Main Writer'),
                                      os.environ.get('AIWF_SESSION_ID', 'workflow-' + work_item_id), int(time.time()))
            entry, receipt_path = _implementation_entry_receipt(blueprint_path, work_item_id, adapter, request)
            if entry.get("status") != "ACTIVE":
                findings.append("ENTRY_BLOCKED")
        except (OSError, ValueError) as exc:
            findings.append(str(exc))

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
            "scoped_receipt": f".agents/state/work-items/{work_item_id}/implementation-entry-receipt.json" if receipt_path else None,
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
