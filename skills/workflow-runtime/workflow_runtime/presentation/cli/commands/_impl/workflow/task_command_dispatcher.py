"""
workflow_runtime/presentation/cli/commands/_impl/workflow/task_command_dispatcher.py

Task command dispatcher for CLI subcommands: task, blueprint, suggest, compact, work-item.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.infrastructure.session.session_io import (
    load_session, save_session_atomic)
from workflow_runtime.presentation.cli.commands._impl import shared_helpers
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    extract_work_item_id_from_text, sync_blueprint_approval_metadata)
from workflow_runtime.application.command_contract import CommandResult, NextAction, emit_result
from workflow_runtime.presentation.cli.commands._impl.workflow.task_state_synchronizer import (
    sync_execution_state_to_session)
from workflow_runtime.presentation.cli.workflow_runtime_shared import (
    update_context_health)


def do_task(args: argparse.Namespace) -> None:
    tasks_file = os.path.join(".agents", "runtime", "parallel-tasks.json")
    os.makedirs(os.path.dirname(tasks_file), exist_ok=True)

    tasks: dict[str, dict[str, Any]] = {}
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
                raw_tasks = data.get("tasks")
                if isinstance(raw_tasks, dict):
                    tasks = cast(dict[str, dict[str, Any]], raw_tasks)
        except Exception:
            pass

    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)

    if subaction == "plan":
        plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
        os.makedirs(os.path.dirname(plan_file), exist_ok=True)
        plan_tasks: list[dict[str, Any]] = []
        if os.path.exists(plan_file):
            try:
                with open(plan_file, "r", encoding="utf-8") as f:
                    data = cast(dict[str, Any], json.load(f))
                    raw_p = data.get("tasks")
                    if isinstance(raw_p, list):
                        plan_tasks = cast(list[dict[str, Any]], raw_p)
            except Exception:
                pass
        for t in plan_tasks:
            tid = t.get("task_id")
            if isinstance(tid, str) and tid:
                tasks[tid] = {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "execution_group": t.get("execution_group", "Group 1")
                }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print("Tasks planned successfully.")

    elif subaction == "start":
        task_id = str(getattr(args, "task_id", "") or "")
        if not task_id:
            print("Error: task_id required.", file=sys.stderr)
            sys.exit(1)
        if task_id not in tasks:
            tasks[task_id] = {}
        tasks[task_id]["status"] = "running"
        tasks[task_id]["started_at"] = datetime.now().astimezone().isoformat()
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print(f"Task {task_id} started.")

    elif subaction == "complete":
        task_id = str(getattr(args, "task_id", "") or "")
        if not task_id:
            print("Error: task_id required.", file=sys.stderr)
            sys.exit(1)
        if task_id not in tasks:
            print(f"Error: task {task_id} not found.", file=sys.stderr)
            sys.exit(1)
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["completed_at"] = datetime.now().astimezone().isoformat()
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print(f"Task {task_id} completed.")

    elif subaction == "fail":
        task_id = str(getattr(args, "task_id", "") or "")
        if not task_id:
            print("Error: task_id required.", file=sys.stderr)
            sys.exit(1)
        if task_id not in tasks:
            tasks[task_id] = {}
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["completed_at"] = datetime.now().astimezone().isoformat()
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print(f"Task {task_id} failed.")

    sync_execution_state_to_session()
def do_blueprint(args: Any) -> int:
    session = load_session()
    if not session:
        return emit_result(CommandResult(
            command="blueprint",
            status="blocked",
            summary="Workflow session is missing.",
            blocking_findings=("session_missing",),
            next_action=NextAction(command="init", required=True),
        ), sys.stdout)

    action = "approve" if getattr(args, "approve", False) else str(getattr(args, "action", "") or "status")
    raw_wi = session.get("work_item")
    wi_dict = cast(dict[str, Any], raw_wi) if isinstance(raw_wi, dict) else {}
    work_item_id = str(getattr(args, "work_item", "") or wi_dict.get("id", ""))
    current_blueprint = session.get("blueprint")
    current_data = current_blueprint if isinstance(current_blueprint, dict) else {}
    bp_path = str(getattr(args, "path", "") or current_data.get("path", ""))
    if not bp_path:
        return emit_result(CommandResult(
            command="blueprint",
            status="invalid_input",
            summary="A blueprint path is required.",
            blocking_findings=("blueprint_path_missing",),
            next_action=NextAction(command="blueprint --path <path>", required=True),
        ), sys.stdout)

    exists = os.path.isfile(bp_path)
    extract_artifact_fn: Any = getattr(shared_helpers, "extract_work_item_id_from_artifact", None)
    parsed_id = extract_work_item_id_from_text(bp_path)
    if exists and not parsed_id and callable(extract_artifact_fn):
        parsed_id = str(extract_artifact_fn(bp_path))
    bp_work_item_id = str(parsed_id or "")
    same_approved_blueprint = (
        current_data.get("path") == bp_path and bool(current_data.get("approved"))
    )
    bp_data: dict[str, Any] = {
        "path": bp_path,
        "exists": exists,
        "approved": bool(current_data.get("approved")) if current_data.get("path") == bp_path else False,
        "approved_at": str(current_data.get("approved_at", "")) if current_data.get("path") == bp_path else "",
        "approved_by": str(current_data.get("approved_by", "")) if current_data.get("path") == bp_path else "",
        "work_item_id": bp_work_item_id or work_item_id
    }
    if getattr(args, "approve", False):
        if not exists:
            return emit_result(CommandResult(
                command="blueprint",
                status="blocked",
                summary="The blueprint file does not exist.",
                data={"blueprint": bp_path},
                blocking_findings=("blueprint_not_found",),
                next_action=NextAction(command="blueprint --path <path>", required=True),
            ), sys.stdout)
        validate_scope_fn: Any = getattr(shared_helpers, "validate_blueprint_scope", None)
        scope_ok = True
        scope_reason = ""
        if callable(validate_scope_fn):
            scope_res: Any = validate_scope_fn(bp_data, work_item_id)
            if isinstance(scope_res, (tuple, list)):
                res_list = cast(list[Any], scope_res)
                if len(res_list) > 0:
                    scope_ok = bool(res_list[0])
                if len(res_list) > 1:
                    scope_reason = str(res_list[1])
        if not scope_ok:
            return emit_result(CommandResult(
                command="blueprint",
                status="blocked",
                summary="Blueprint scope does not match the active work item.",
                blocking_findings=(scope_reason or "blueprint_scope_mismatch",),
                next_action=NextAction(command="blueprint --path <path>", required=True),
            ), sys.stdout)
        bp_data["approved"] = True
        bp_data["approved_at"] = datetime.now().astimezone().isoformat()
        bp_data["approved_by"] = "user"
        bp_data["approval_source"] = "runtime_blueprint_approve"

        bp_data["sha256"] = sync_blueprint_approval_metadata(
            bp_path,
            approved_at=str(bp_data["approved_at"]),
            approved_by=str(bp_data["approved_by"]),
        )
        session["blueprint"] = bp_data
        session["status"] = "in_progress"
        if same_approved_blueprint:
            session["current_step"] = "Blueprint approval state synchronized."
            if (
                int(session.get("checkpoint", 1) or 1) >= 9
                and session.get("suggested_next_skill") == "implementation-to-release"
            ):
                session["current_skill"] = "implementation-to-release"
                session["current_command"] = str(
                    session.get("suggested_next_command") or "release"
                )
        else:
            session["current_step"] = "Blueprint approved; implementation is ready."
            session["active_phase"] = "implementation"
            session["current_skill"] = "blueprint-to-implementation"
            session["current_command"] = "implement"
            session["checkpoint"] = max(int(session.get("checkpoint", 1) or 1), 6)
        update_context_health(session)
        save_session_atomic(session)
    elif action in ("generate", "freeze"):
        session["blueprint"] = bp_data
        update_context_health(session)
        save_session_atomic(session)

    result_status = "success" if exists else "blocked"
    findings = () if exists else ("blueprint_not_found",)
    return emit_result(CommandResult(
        command="blueprint",
        status=result_status,
        summary="Blueprint approved and persisted." if getattr(args, "approve", False) else "Blueprint inspected.",
        data={
            "path": bp_path,
            "exists": exists,
            "approved": bp_data["approved"],
            "work_item_id": bp_data["work_item_id"],
            "action": action,
        },
        artifacts=(bp_path,) if exists else (),
        blocking_findings=findings,
        side_effects=(((f".agents/state/work-items/{work_item_id}/approvals.json" if work_item_id else ".agents/state/approvals.json"),) if getattr(args, "approve", False) else ()),
        next_action=NextAction(
            skill="blueprint-to-implementation" if bp_data["approved"] else None,
            command="implement --blueprint <path>" if bp_data["approved"] else "blueprint --path <path> --approve",
            required=not bp_data["approved"],
        ),
    ), sys.stdout)
def do_suggest(args: Any) -> int:
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)

    raw_sug = session.get("suggestion_gate")
    suggestion: dict[str, Any] = cast(dict[str, Any], raw_sug) if isinstance(raw_sug, dict) else {
        "active": False,
        "raw_request": "",
        "classification": "",
        "recommended_skill": "",
        "options": [],
        "status": "idle"
    }

    req_arg = getattr(args, "request", None)
    if req_arg:
        suggestion["raw_request"] = str(req_arg)
        suggestion["active"] = True
        suggestion["status"] = "waiting_for_user_confirmation"

    class_arg = getattr(args, "classification", None)
    if class_arg:
        suggestion["classification"] = str(class_arg)

    rec_arg = getattr(args, "recommend", None)
    if rec_arg:
        suggestion["recommended_skill"] = str(rec_arg)

    opt_arg = getattr(args, "options", None)
    if opt_arg:
        suggestion["options"] = [o.strip() for o in str(opt_arg).split(",")]

    stat_arg = getattr(args, "status", None)
    if stat_arg:
        stat_str = str(stat_arg)
        suggestion["status"] = stat_str
        if stat_str in ["confirmed", "idle", "rejected"]:
            suggestion["active"] = False

    choose_arg = getattr(args, "choose", None)
    if choose_arg:
        choice = str(choose_arg).strip().lower()
        if choice in ["y", "yes", "proceed", "continue"]:
            suggestion["status"] = "confirmed"
            suggestion["active"] = False
            print("Suggestion confirmed.")
        elif choice in ["n", "no"]:
            suggestion["status"] = "rejected"
            suggestion["active"] = False
            print("Suggestion rejected.")
        else:
            try:
                idx = int(choice) - 1
                raw_opts = suggestion.get("options", [])
                opts_list = [str(o) for o in cast(list[Any], raw_opts)] if isinstance(raw_opts, list) else []
                if 0 <= idx < len(opts_list):
                    suggestion["recommended_skill"] = opts_list[idx]
                    suggestion["status"] = "confirmed"
                    suggestion["active"] = False
                    print(f"Option {choice} selected: {suggestion['recommended_skill']}.")
                else:
                    print(f"Error: Invalid option index {choice}.", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"Error: Invalid choice {choice}.", file=sys.stderr)
                sys.exit(1)

    if not choose_arg and bool(suggestion.get("active")):
        try:
            from workflow_runtime.shared.utils import (is_stdin_ready,
                                                        prompt_select)
            if os.environ.get("TESTING") == "1" and not is_stdin_ready():
                pass
            else:
                raw_opts = suggestion.get("options")
                opts_list = [str(o) for o in cast(list[Any], raw_opts)] if isinstance(raw_opts, list) else []
                if opts_list:
                    default_opt = str(suggestion.get("recommended_skill", ""))
                    if default_opt not in opts_list:
                        default_opt = opts_list[0]
                    choice = str(prompt_select(f"Which workflow/skill should be used for request '{suggestion.get('raw_request')}'?", opts_list, default=default_opt))
                    suggestion["recommended_skill"] = choice
                    suggestion["status"] = "confirmed"
                    suggestion["active"] = False
                    print(f"Option selected: {choice}")
                elif suggestion.get("recommended_skill"):
                    opts = ["Yes", "No"]
                    choice = str(prompt_select(f"Confirm using skill '{suggestion.get('recommended_skill')}' for request '{suggestion.get('raw_request')}'?", opts, default="Yes"))
                    if choice == "Yes":
                        suggestion["status"] = "confirmed"
                    else:
                        suggestion["status"] = "rejected"
                    suggestion["active"] = False
                    print(f"Suggestion {suggestion['status']}.")
        except Exception:
            pass

    orchestrator_state: dict[str, Any] = {
        "active": suggestion.get("active", False),
        "raw_request": suggestion.get("raw_request", ""),
        "classification": suggestion.get("classification", ""),
        "recommended_skill": suggestion.get("recommended_skill", ""),
        "recommended_command": "",
        "options": suggestion.get("options", []),
        "selected_skill": suggestion.get("recommended_skill") if suggestion.get("status") == "confirmed" else "",
        "selected_command": "",
        "routing_status": "waiting_for_user",
        "reason": suggestion.get("reason", "")
    }

    def map_cmd(skill_name: str) -> str:
        if not skill_name: return ""
        if skill_name == "quick-fix": return "fix"
        if skill_name == "quick-feature": return "feature"
        if skill_name == "brainstorming": return "brainstorm"
        if skill_name == "project-rag-search": return "search"
        if skill_name == "project-memory-bootstrap": return "bootstrap"
        if skill_name == "project-memory-update": return "update"
        if skill_name == "blueprint-to-implementation": return "implement"
        if skill_name == "implementation-to-debug": return "debug"
        if skill_name == "debug-to-verify": return "verify"
        if skill_name == "implementation-to-release": return "release"
        return ""

    rec_skill = str(orchestrator_state.get("recommended_skill", ""))
    sel_skill = str(orchestrator_state.get("selected_skill", ""))

    orchestrator_state["recommended_command"] = map_cmd(rec_skill)
    if sel_skill:
        orchestrator_state["selected_command"] = map_cmd(sel_skill)
        orchestrator_state["routing_status"] = "dispatched"
    elif not orchestrator_state.get("active"):
        orchestrator_state["routing_status"] = "stopped"

    session["orchestrator"] = orchestrator_state
    session["suggestion_gate"] = suggestion
    update_context_health(session)
    save_session_atomic(session)

    raw_wf = session.get("workflow")
    wf_dict = cast(dict[str, Any], raw_wf) if isinstance(raw_wf, dict) else {}
    raw_bp = session.get("blueprint")
    bp_dict = cast(dict[str, Any], raw_bp) if isinstance(raw_bp, dict) else {}

    output_dict = {
        "suggested_next_skill": orchestrator_state.get("recommended_skill") or wf_dict.get("suggested_next_skill") or "",
        "suggested_next_command": orchestrator_state.get("recommended_command") or wf_dict.get("suggested_next_command") or "",
        "reason": orchestrator_state.get("reason") or (
            "Blueprint approved. Proceeding to implementation." if bp_dict.get("approved") else "Provide new instruction."
        ),
        "expected_input": bp_dict.get("path") or ""
    }
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))
    return 0
def do_compact(_args: argparse.Namespace) -> None:
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)

    stash_ref = ""
    try:
        res = subprocess.run(["git", "stash", "create"], capture_output=True, text=True, check=True)
        stash_hash = res.stdout.strip()
        if stash_hash:
            _ = subprocess.run(["git", "stash", "store", "-m", "Rollover Context Auto-Stash", stash_hash], check=True)
            stash_ref = "stash@{0}"
            print(f"Git auto-stash created: {stash_ref}")
    except Exception:
        pass

    plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
    execution_mode = "pending"
    recommended_mode = "parallel"
    approved = False
    implementation_execution_mode = "pending"
    parallel_allowed_phase = "implementation"
    parallel_allowed = False
    if os.path.exists(plan_file):
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = cast(dict[str, Any], json.load(f))
                execution_mode = str(plan_data.get("execution_mode", "pending"))
                recommended_mode = str(plan_data.get("recommended_mode", "parallel"))
                approved = bool(plan_data.get("approved", False))
                implementation_execution_mode = str(plan_data.get("implementation_execution_mode", "pending"))
                parallel_allowed_phase = str(plan_data.get("parallel_allowed_phase", "implementation"))
                parallel_allowed = bool(plan_data.get("parallel_allowed", False))
        except Exception:
            pass

    tasks_file = os.path.join(".agents", "runtime", "parallel-tasks.json")
    parallel_groups: list[str] = []
    running_agents: list[str] = []
    queued_agents: list[str] = []
    blocked_agents: list[str] = []
    waiting_dependencies: list[str] = []

    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks_data = cast(dict[str, Any], json.load(f))
                raw_tasks = tasks_data.get("tasks")
                tasks: dict[str, Any] = cast(dict[str, Any], raw_tasks) if isinstance(raw_tasks, dict) else {}
                for tid, tinfo in tasks.items():
                    if isinstance(tinfo, dict):
                        t_dict = cast(dict[str, Any], tinfo)
                        status = str(t_dict.get("status", "pending"))
                        group = str(t_dict.get("execution_group", ""))
                        if group and group not in parallel_groups:
                            parallel_groups.append(group)
                        if status == "running":
                            running_agents.append(str(tid))
                        elif status == "pending":
                            queued_agents.append(str(tid))
                        elif status == "blocked":
                            blocked_agents.append(str(tid))
        except Exception:
            pass

    snapshot_file = os.path.join(".agents", "runtime", "context_snapshot.json")
    os.makedirs(os.path.dirname(snapshot_file), exist_ok=True)

    raw_cs = session.get("current_skill")
    raw_cc = session.get("current_command")
    raw_cstep = session.get("current_step")

    snapshot: dict[str, Any] = {
        "checkpoint": session.get("checkpoint", 1),
        "current_skill": str(raw_cs) if raw_cs else "",
        "current_command": str(raw_cc) if raw_cc else "",
        "current_step": str(raw_cstep) if raw_cstep else "",
        "active_feature_id": "FIX-014",
        "git_stash_ref": stash_ref,
        "rollover_requested_at": datetime.now().astimezone().isoformat(),
        "execution_mode": execution_mode,
        "recommended_mode": recommended_mode,
        "approved": approved,
        "implementation_execution_mode": implementation_execution_mode,
        "parallel_allowed_phase": parallel_allowed_phase,
        "parallel_allowed": parallel_allowed,
        "parallel_groups": parallel_groups,
        "running_agents": running_agents,
        "queued_agents": queued_agents,
        "blocked_agents": blocked_agents,
        "waiting_dependencies": waiting_dependencies
    }

    try:
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        print(f"Context snapshot written successfully to {snapshot_file}")
    except IOError as e:
        print(f"Error: failed to write snapshot: {e}", file=sys.stderr)
        sys.exit(1)
def do_work_item_cached(args: argparse.Namespace) -> None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from workflow_runtime.application.verification.validator import (
        detect_work_item_cached)
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    if subaction == "detect":
        work_item = detect_work_item_cached()
        print(json.dumps(work_item, indent=2))
    else:
        print(f"Unknown work-item subaction: {subaction}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "do_task",
    "do_blueprint",
    "do_suggest",
    "do_compact",
    "do_work_item_cached",
]
