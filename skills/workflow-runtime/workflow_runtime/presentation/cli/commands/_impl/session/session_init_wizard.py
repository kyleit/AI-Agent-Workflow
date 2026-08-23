from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.analysis.fingerprint import \
    calculate_project_fingerprint
from workflow_runtime.infrastructure.persistence.lease import WorkflowLease
from workflow_runtime.infrastructure.session.session_io import (
    load_session, save_session_atomic)
from workflow_runtime.infrastructure.session.state_sync import \
    deconstruct_state
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    ForbiddenAISourceError, extract_work_item_id_from_text,
    get_current_project_context, is_telegram_daemon_running,
    sync_analysis_agents_to_session)
from workflow_runtime.presentation.cli.workflow_runtime_shared import \
    update_context_health


def do_init(args: Any) -> None:
    session: dict[str, Any] = load_session() or {}

    has_project_args = (
        getattr(args, "name", None) is not None or
        getattr(args, "path", None) is not None or
        getattr(args, "non_interactive", False) or
        getattr(args, "config", None) is not None or
        getattr(args, "dry_run", False) or
        getattr(args, "resume", False)
    )
    config_exists = os.path.exists(os.path.join(getattr(args, "path", None) or ".", ".agents", "project.config.json"))
    if (has_project_args or not config_exists) and not getattr(args, "permission", None):
        if not sys.stdin.isatty():
            pass
    else:
        session["current_logs"] = ["> Initialization completed successfully (loaded from cache)."]
        session["updated_at"] = datetime.now().astimezone().isoformat()

    # Nạp tĩnh quyền từ permissions.json
    from workflow_runtime.infrastructure.session.session import \
        load_project_permissions
    permissions = load_project_permissions()
    if not permissions or not permissions.get("initialized"):
        print("Error: Project permission mode has not been initialized.", file=sys.stderr)
        print("Please run 'python workflow_runtime.py permissions init' manually first.", file=sys.stderr)
        sys.exit(1)

    mode = permissions.get("mode", "sandbox")
    session["permission_mode"] = mode
    session["permission_mode_selected_at"] = permissions.get("updated_at")
    session["permission_mode_selected_by"] = permissions.get("updated_by", "user")

    update_context_health(session)
    save_session_atomic(session)
    print(f"Session initialized with permission_mode={mode}.")

    # Load and validate runtime policy configuration
    from workflow_runtime.infrastructure.session.session_lock import \
        load_runtime_policy
    try:
        load_runtime_policy(validate=True)
    except Exception as e:
        print(f"Error loading/validating runtime policy: {e}", file=sys.stderr)
        sys.exit(1)

    # Integrate Workspace Doctor
    print("Running Workspace Doctor...")
    try:
        res_json = subprocess.check_output([sys.executable, "-m", "workflow_runtime", "doctor"]).decode().strip()
        doctor_res = cast(dict[str, Any], json.loads(res_json)) if res_json else {}
    except Exception:
        doctor_res = {
            "status": "FAIL",
            "runtime_mode": "session",
            "permissions": "FAIL",
            "skills": "FAIL",
            "workflow_supervisor": "FAIL"
        }

    if doctor_res.get("status") != "READY":
        print(f"Workspace validation failed! Doctor report: {json.dumps(doctor_res, indent=2)}", file=sys.stderr)
        sys.exit(1)

    runtime_mode = doctor_res.get("runtime_mode", "session")
    session["runtime_mode"] = runtime_mode
    save_session_atomic(session)

    # Sentinel tracking vars
    _daemon_running: bool = False
    _daemon_pid: int | None = None
    _daemon_warn: str = ""
    _memory_loaded: bool = False
    _memory_last_updated: str = "N/A"
    _memory_git_hash: str = ""
    _memory_chars: int = 0
    _memory_warn: str = ""

    # Check Telegram daemon
    try:
        pid_file = os.path.expanduser("~/.aiwf/telegram-daemon.pid")
        _daemon_running, _daemon_pid = is_telegram_daemon_running(pid_file)

        daemon_state_path = os.path.join(".agents", "state", "daemon.json")
        daemon_state = {
            "telegram_daemon": {
                "running": _daemon_running,
                "pid": _daemon_pid,
                "pid_file": "~/.aiwf/telegram-daemon.pid"
            },
            "updated_at": datetime.now().astimezone().isoformat()
        }
        try:
            os.makedirs(os.path.dirname(daemon_state_path), exist_ok=True)
            with open(daemon_state_path, "w", encoding="utf-8") as f:
                json.dump(daemon_state, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        if _daemon_running:
            monitor_cmd = [sys.executable, "-m", "workflow_runtime", "telegram", "monitor-inbox"]
            try:
                if os.name == "nt":
                    subprocess.Popen(
                        monitor_cmd,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                else:
                    subprocess.Popen(
                        monitor_cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
            except Exception as ex:
                _daemon_warn = str(ex)
    except Exception as ex:
        _daemon_warn = str(ex)

    try:
        memory_summary_path = os.path.join(".agents", "memory", "project-summary.md")
        memory_state_path = os.path.join(".agents", "memory", "memory-state.json")
        memory_meta: dict[str, Any] = {}

        if os.path.exists(memory_state_path):
            with open(memory_state_path, "r", encoding="utf-8") as f:
                loaded_meta = json.load(f)
                if isinstance(loaded_meta, dict):
                    memory_meta = cast(dict[str, Any], loaded_meta)

        if os.path.exists(memory_summary_path):
            with open(memory_summary_path, "r", encoding="utf-8") as f:
                memory_content = f.read()
            session["memory_summary"] = memory_content
            session["memory_status"] = "loaded"
            session["memory_last_updated"] = memory_meta.get("last_updated_at", "unknown")
            session["memory_git_hash"] = memory_meta.get("last_git_hash", "")
            save_session_atomic(session)
            _memory_loaded = True
            _memory_last_updated = str(memory_meta.get("last_updated_at", "N/A"))
            _memory_git_hash = str(memory_meta.get("last_git_hash", ""))[:8]
            _memory_chars = len(memory_content)
        else:
            session["memory_status"] = "uninitialized"
            save_session_atomic(session)
    except Exception as ex:
        _memory_warn = str(ex)
        session["memory_status"] = "error"
        save_session_atomic(session)

    # ── Init Report ────────────────────────────────────────────────────────────
    _git_branch    = str(session.get("git_branch", "unknown"))
    _perm_mode     = str(session.get("permission_mode", "sandbox"))
    _rt_mode       = str(session.get("runtime_mode", "session"))
    _conv_id       = str(session.get("conversation_id", "N/A"))
    _project_id    = str(session.get("project_id", "ai-skill-framework"))
    _version       = str(session.get("project_version", "N/A"))

    _tg_status     = f"RUNNING  (PID {_daemon_pid}, inbox monitor armed)" if _daemon_running else "INACTIVE (inbox monitor not started)"
    _mem_status: str
    if _memory_loaded:
        _mem_status = f"LOADED   {_memory_chars:,} chars | updated {_memory_last_updated} | git {_memory_git_hash}"
    elif _memory_warn:
        _mem_status = f"ERROR    {_memory_warn}"
    else:
        _mem_status = "MISSING  — run 'aiwf memory init'"

    print("")
    print("=" * 60)
    print("  Initialization Report")
    print("=" * 60)
    print(f"  Project       : {_project_id}  v{_version}")
    print(f"  Conversation  : {_conv_id}")
    print(f"  Git branch    : {_git_branch}")
    print(f"  Permission    : {_perm_mode}")
    print(f"  Runtime mode  : {_rt_mode}")
    print("-" * 60)
    print(f"  Memory        : {_mem_status}")
    print(f"  Telegram      : {_tg_status}")
    if _daemon_warn:
        print(f"  Telegram WARN : {_daemon_warn}")
    print("-" * 60)
    print("  Workspace     : READY")
    print("  Runtime       : SESSION_MODE")
    print("  Supervisor    : READY")
    print("=" * 60)
    print("")

    # Update runtime.json status to completed
    state_dir = os.path.join(".agents", "state")
    runtime_path = os.path.join(state_dir, "runtime.json")
    runtime_data: dict[str, Any] = {}
    try:
        if os.path.exists(runtime_path):
            with open(runtime_path, "r", encoding="utf-8") as f:
                loaded_rt = json.load(f)
                if isinstance(loaded_rt, dict):
                    runtime_data = cast(dict[str, Any], loaded_rt)
    except Exception:
        pass

    runtime_data.update({
        "status": "completed",
        "current_step": "Initialization Complete",
        "checkpoint": 1,
        "updated_at": datetime.now().astimezone().isoformat()
    })
    try:
        with open(runtime_path, "w", encoding="utf-8") as f:
            json.dump(runtime_data, f, indent=2)
    except Exception:
        pass

    try:
        conv_id = str(os.environ.get("AIWF_CONVERSATION_ID") or session.get("conversation_id") or "CONV-DEFAULT")
        print(f"[INFO] Initialized session for conversation: {conv_id}")
    except Exception:
        pass


__all__ = [
    "do_init",
    "ForbiddenAISourceError",
    "WorkflowLease",
    "calculate_project_fingerprint",
    "deconstruct_state",
    "extract_work_item_id_from_text",
    "get_current_project_context",
    "sync_analysis_agents_to_session",
]
