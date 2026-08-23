from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.infrastructure.events.heartbeat import print_heartbeat
from workflow_runtime.infrastructure.persistence.checkpoint import (
    get_checkpoint_name)
from workflow_runtime.infrastructure.persistence.lease import WorkflowLease
from workflow_runtime.infrastructure.session.session_io import (
    load_session, save_session_atomic)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    get_current_project_context, sync_analysis_agents_to_session)
from workflow_runtime.presentation.cli.workflow_runtime_shared import (
    update_context_health)


def validate_blueprint_scope(bp: dict[str, Any], work_item_id: str) -> tuple[bool, str]:
    if not bp:
        return False, "Blueprint missing"
    wi = str(bp.get("work_item_id") or bp.get("id") or "")
    if wi and wi != work_item_id:
        return False, f"Blueprint work item {wi} does not match {work_item_id}"
    return True, "Scope valid"


def do_start(args: Any) -> int:
    session: dict[str, Any] = load_session() or {"workspace": {"path": ".", "valid": True}}

    raw_wi = session.get("work_item")
    wi_dict = cast(dict[str, Any], raw_wi) if isinstance(raw_wi, dict) else {}
    work_item_id = str(wi_dict.get("id", "unknown"))

    skill_name = str(getattr(args, "skill", "") or "")
    chk_val = getattr(args, "checkpoint", None)
    checkpoint = int(chk_val) if chk_val is not None else None

    if not WorkflowLease.acquire(skill_name, work_item_id):
        print("Another workflow is already running.", file=sys.stderr)
        print("Do not continue.", file=sys.stderr)
        sys.exit(1)

    is_impl = (skill_name == "blueprint-to-implementation") or (checkpoint is not None and checkpoint >= 6)
    if is_impl:
        raw_bp = session.get("blueprint")
        bp: dict[str, Any] = cast(dict[str, Any], raw_bp) if isinstance(raw_bp, dict) else {}
        scope_ok, scope_reason = validate_blueprint_scope(bp, work_item_id)
        if not bool(bp.get("approved")) or not scope_ok:
            print(f"Error: Cannot start implementation. Technical Design Blueprint is not approved for {work_item_id}. {scope_reason}", file=sys.stderr)
            WorkflowLease.release()
            sys.exit(1)

    session["status"] = "in_progress"
    if checkpoint is not None:
        session["checkpoint"] = checkpoint
    session["current_skill"] = skill_name
    session["current_command"] = str(getattr(args, "command", "") or "")
    session["current_step"] = str(getattr(args, "step", "") or "")
    session["autonomous_delivery"] = bool(getattr(args, "autonomous", False))
    session["current_logs"] = [f"> Starting {skill_name}..."]

    update_context_health(session)
    save_session_atomic(session)

    try:
        from workflow_runtime.shared.utils import log_phase_transition_event
        log_phase_transition_event("idle", skill_name, "success")
    except Exception:
        pass

    print(f"Skill {skill_name} started.")
    return 0


def do_step(args: Any) -> int:
    WorkflowLease.heartbeat()

    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    session["current_step"] = str(getattr(args, "step", "") or "")
    raw_logs = session.get("current_logs")
    current_logs: list[str] = cast(list[str], raw_logs) if isinstance(raw_logs, list) else []
    log_msg = getattr(args, "log", None)
    if log_msg:
        current_logs.append(str(log_msg))
    session["current_logs"] = current_logs
    update_context_health(session)
    save_session_atomic(session)
    return 0


def do_complete(args: Any) -> int:
    WorkflowLease.release(force=True)

    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    session["status"] = "completed"
    chk_val = getattr(args, "checkpoint", None)
    checkpoint = int(chk_val) if chk_val is not None else None
    if checkpoint is not None:
        session["checkpoint"] = checkpoint
    step_val = getattr(args, "step", None)
    if step_val:
        session["current_step"] = str(step_val)
    else:
        chk = checkpoint or int(session.get("checkpoint", 1) or 1)
        session["current_step"] = get_checkpoint_name(chk)
    session["suggested_next_skill"] = str(getattr(args, "next_skill", "") or "")
    session["suggested_next_command"] = str(getattr(args, "next_command", "") or "")

    raw_logs = session.get("current_logs")
    current_logs: list[str] = cast(list[str], raw_logs) if isinstance(raw_logs, list) else []
    current_logs.append("> Completed successfully.")
    session["current_logs"] = current_logs

    update_context_health(session)
    save_session_atomic(session)

    try:
        from workflow_runtime.shared.utils import log_phase_transition_event
        next_sk = str(getattr(args, "next_skill", "") or "completed")
        log_phase_transition_event(str(session.get("current_skill", "unknown")), next_sk, "success")
    except Exception:
        pass

    analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
    if os.path.exists(analysis_file):
        try:
            os.remove(analysis_file)
        except Exception:
            pass
    sync_analysis_agents_to_session()

    print("Step completed.")
    return 0


def do_fail(args: Any) -> int:
    WorkflowLease.release(force=True)

    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    session["status"] = "failed"
    session["current_step"] = str(getattr(args, "step", "") or "")

    raw_logs = session.get("current_logs")
    current_logs: list[str] = cast(list[str], raw_logs) if isinstance(raw_logs, list) else []
    log_msg = getattr(args, "log", None)
    if log_msg:
        current_logs.append(f"Error: {log_msg}")
    session["current_logs"] = current_logs

    update_context_health(session)
    save_session_atomic(session)
    print("Step failed.")
    return 0


def do_heartbeat(_args: Any) -> int:
    session = load_session()
    if not session:
        print(json.dumps({
            "status": "no_session",
            "message": "No active session. Run aiwf init to start.",
            "heartbeat": "idle",
        }))
        return 0
    update_context_health(session)
    print_heartbeat(session)
    return 0


def do_lock(args: argparse.Namespace) -> None:
    subaction = str(getattr(args, 'action', None) or getattr(args, 'subaction', None) or "")
    if subaction == "inspect":
        status = WorkflowLease.inspect()
        print(json.dumps(status, indent=2))
        return

    elif subaction == "recover":
        status = WorkflowLease.inspect()
        if not bool(status.get("active")):
            WorkflowLease.release()
            print("Stale workflow lock successfully recovered.")
        else:
            print("Active workflow lock is running. Cannot recover.", file=sys.stderr)
            sys.exit(1)
        return

    elif subaction == "release" and getattr(args, "stale_only", False):
        status = WorkflowLease.inspect()
        if not bool(status.get("active")):
            WorkflowLease.release()
            print("Stale workflow lock released.")
        else:
            print("Lease is active and valid. Will not release stale lock.", file=sys.stderr)
            sys.exit(1)
        return

    locks_file = os.path.join(".agents", "runtime", "file-locks.json")
    os.makedirs(os.path.dirname(locks_file), exist_ok=True)

    locks: dict[str, dict[str, Any]] = {}
    if os.path.exists(locks_file):
        try:
            with open(locks_file, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
                raw_locks = data.get("locks")
                if isinstance(raw_locks, dict):
                    locks = cast(dict[str, dict[str, Any]], raw_locks)
        except Exception:
            pass

    if subaction == "acquire":
        task_id = str(getattr(args, "task_id", "") or "")
        files_arg = str(getattr(args, "files", "") or "")
        if not task_id or not files_arg:
            print("Error: task_id and files are required.", file=sys.stderr)
            sys.exit(1)
        files = [f.strip() for f in files_arg.split(",")]

        conflicting: list[tuple[str, Any]] = []
        for file in files:
            if file in locks and locks[file].get("task_id") != task_id:
                conflicting.append((file, locks[file].get("task_id")))

        if conflicting:
            print(f"Error: lock acquisition failed. Files locked by other tasks: {conflicting}", file=sys.stderr)
            sys.exit(1)

        for file in files:
            locks[file] = {
                "task_id": task_id,
                "acquired_at": datetime.now().astimezone().isoformat()
            }

        with open(locks_file, "w", encoding="utf-8") as f:
            json.dump({"locks": locks}, f, indent=2, ensure_ascii=False)
        print(f"Locks acquired for task {task_id} on: {files}")

    elif subaction == "release":
        task_id = str(getattr(args, "task_id", "") or "")
        if not task_id:
            print("Error: task_id is required.", file=sys.stderr)
            sys.exit(1)
        released: list[str] = []
        for file, lock in list(locks.items()):
            if bool(lock) and lock.get("task_id") == task_id:
                del locks[file]
                released.append(file)
        with open(locks_file, "w", encoding="utf-8") as f:
            json.dump({"locks": locks}, f, indent=2, ensure_ascii=False)
        print(f"Locks released for task {task_id}: {released}")

    elif subaction == "list":
        print(json.dumps({"locks": locks}, indent=2))


def do_status_action(_args: Any) -> None:
    session = load_session() or {}
    lease_status = WorkflowLease.inspect()
    status_data = {
        "project": get_current_project_context(),
        "session": {
            "checkpoint": session.get("checkpoint", 1),
            "status": session.get("status", "unknown"),
            "current_skill": session.get("current_skill", "unknown"),
            "current_command": session.get("current_command", "unknown"),
            "current_step": session.get("current_step", "unknown"),
            "context_health": session.get("context_health", "unknown")
        },
        "lease": lease_status
    }
    print(json.dumps(status_data, indent=2))


def do_resume_action(_args: Any) -> None:
    from workflow_runtime.application.workflow.workflow_state import (
        resume_session)
    res = resume_session()
    print(json.dumps(res, indent=2))
    if res.get("status") != "success":
        sys.exit(1)


__all__ = [
    "do_start",
    "do_step",
    "do_complete",
    "do_fail",
    "do_heartbeat",
    "do_lock",
    "do_status_action",
    "do_resume_action",
]
