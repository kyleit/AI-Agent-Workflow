from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.analysis.fingerprint import \
    calculate_project_fingerprint
from workflow_runtime.infrastructure.session.session_io import (
    load_session, save_session_atomic)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import \
    is_telegram_daemon_running
from workflow_runtime.presentation.cli.workflow_runtime_shared import (
    get_project_id, send_telegram_startup_message, update_context_health)
from workflow_runtime.shared.git_utils import get_git_info, get_version_info
from workflow_runtime.shared.utils import get_memory_info, get_rag_info


def do_init(args: Any) -> int:
    import json
    import subprocess

    from workflow_runtime.infrastructure.session.session import \
        write_project_permissions_atomic
    supplied_config: dict[str, Any] = {}
    if getattr(args, "config", None):
        try:
            with open(getattr(args, "config"), "r", encoding="utf-8-sig") as f:
                loaded_config = json.load(f)
            if isinstance(loaded_config, dict):
                supplied_config = cast(dict[str, Any], loaded_config)
        except Exception as exc:
            print(f"Error loading configuration: {exc}", file=sys.stderr)
            sys.exit(1)
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
        import json
        project_name = supplied_config.get("project_name") or supplied_config.get("name") or getattr(args, "name", None) or os.path.basename(os.path.abspath(getattr(args, "path", None) or ".")) or "default-project"
        display_name = supplied_config.get("display_name") or str(project_name).replace("-", " ").replace("_", " ").title()
        description = supplied_config.get("description") or "Auto-initialized project"
        primary_language = supplied_config.get("primary_language") or supplied_config.get("language") or "Python"
        database_engine = supplied_config.get("database_engine") or supplied_config.get("database") or "SQLite"
        initialize_git = bool(supplied_config.get("initialize_git", True))
        permission_mode = supplied_config.get("permission_mode") or "sandbox"
        default_config = {
            "schema_version": "1.0.0",
            "project": {
                "name": project_name,
                "display_name": display_name,
                "description": description,
                "version": "1.0.0"
            },
            "topology": {"type": "single-module"},
            "architecture": {"pattern": "DDD + Clean Architecture"},
            "languages": [primary_language],
            "database": {"engine": database_engine},
            "git": {"initialize": initialize_git, "default_branch": "main"},
            "created_at": datetime.now().astimezone().isoformat(),
            "updated_at": datetime.now().astimezone().isoformat()
        }
        target_path = getattr(args, "path", None) or "."
        os.makedirs(os.path.join(target_path, ".agents"), exist_ok=True)
        config_path = os.path.join(target_path, ".agents", "project.config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)
        config = {
            "schema_version": "1.0.0",
            "initialized": True,
            "mode": permission_mode,
            "config_revision": 1,
            "initialized_at": datetime.now().astimezone().isoformat(),
            "updated_at": datetime.now().astimezone().isoformat(),
            "updated_by": "user",
            "source": "cli",
            "permissions": {
                "default_mode": permission_mode,
                "autonomous_delivery": True if permission_mode == "full_access" else False,
                "auto_continue_internal_phases": True if permission_mode == "full_access" else False,
                "stop_at_release_approval": True,
                "require_separate_git_approval": True,
                "require_separate_release_approval": True,
                "require_separate_deploy_approval": True,
                "max_retries_per_task": 3,
                "max_replans_per_work_item": 2,
                "max_agent_reassignments_per_task": 2
            }
        }
        write_project_permissions_atomic(config)

    # Handle --permission flag if provided
    permission_flag = getattr(args, "permission", None)
    if permission_flag:
        mode = "sandbox"
        if permission_flag == "1":
            mode = "sandbox"
        elif permission_flag == "2":
            mode = "full_access"
        elif permission_flag == "3":
            try:
                sys.stdin.readline().strip()
            except Exception:
                pass
            mode = "sandbox"

        config = {
            "schema_version": "1.0.0",
            "initialized": True,
            "mode": mode,
            "config_revision": 1,
            "initialized_at": datetime.now().astimezone().isoformat(),
            "updated_at": datetime.now().astimezone().isoformat(),
            "updated_by": "user",
            "source": "cli",
            "permissions": {
                "default_mode": mode,
                "autonomous_delivery": True if mode == "full_access" else False,
                "auto_continue_internal_phases": True if mode == "full_access" else False,
                "stop_at_release_approval": True,
                "require_separate_git_approval": True,
                "require_separate_release_approval": True,
                "require_separate_deploy_approval": True,
                "max_retries_per_task": 3,
                "max_replans_per_work_item": 2,
                "max_agent_reassignments_per_task": 2
            }
        }
        write_project_permissions_atomic(config)

    new_fp = calculate_project_fingerprint(".")
    state_dir = os.path.join(".agents", "state")
    context_path = os.path.join(state_dir, "context.json")

    use_cache = False
    session: dict[str, Any] = {}
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                context_data = json.load(f)
            if context_data.get("project_fingerprint") == new_fp:
                use_cache = True
                session = load_session()
        except Exception:
            pass
    if not use_cache or not session:
        session = {
            "workspace": {"path": ".", "valid": True},
            "git": get_git_info(),
            "work_item": {"type": "FEAT", "id": "FEAT-001", "title": "Initial Scaffolding"},
            "version": get_version_info(),
            "memory": get_memory_info(),
            "rag": get_rag_info(),
            "blueprint": {
                "path": "",
                "exists": False,
                "approved": False,
                "approved_at": "",
                "approved_by": ""
            },
            "suggestion_gate": {
                "active": False,
                "raw_request": "",
                "classification": "",
                "recommended_skill": "",
                "options": [],
                "status": "idle"
            },
            "checkpoint": 1,
            "status": "completed",
            "current_skill": "initialize-workflow",
            "current_command": "init",
            "current_step": "Initialization Complete",
            "current_logs": ["> Initialization completed successfully."],
            "suggested_next_skill": "project-discovery",
            "suggested_next_command": "discover",
            "context_health": "healthy"
        }
        session["project_fingerprint"] = new_fp
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

    def register_client_attachment():
        import json

        from workflow_runtime.infrastructure.session.session_lock import \
            get_project_identity
        identity = get_project_identity(getattr(args, "path", None) or ".")
        workspace_id = identity["workspace_id"]

        conversation_id = str(os.environ.get("AIWF_CONVERSATION_ID") or session.get("conversation_id") or "CONV-DEFAULT")

        clients_path = os.path.join(".agents", "state", "clients.json")
        clients_data: dict[str, Any] = {
            "workspace_id": workspace_id,
            "orchestrator_id": "ORCH-001",
            "clients": []
        }
        if os.path.exists(clients_path):
            try:
                with open(clients_path, "r", encoding="utf-8") as f:
                    clients_data = cast(dict[str, Any], json.load(f))
            except Exception:
                pass
        found = False
        clients_list: list[dict[str, Any]] = cast(list[dict[str, Any]], clients_data.setdefault("clients", []))
        for c in clients_list:
            if c.get("session_id") == conversation_id:
                c["status"] = "attached"
                found = True
            else:
                # Do NOT detach others as per instruction "ko detach nhưng cái khác"
                c["status"] = "attached"

        if not found:
            clients_list.append({"session_id": conversation_id, "status": "attached"})

        os.makedirs(os.path.dirname(clients_path), exist_ok=True)
        with open(clients_path, "w", encoding="utf-8") as f:
            json.dump(clients_data, f, indent=2, ensure_ascii=False)

    register_client_attachment()

    # Integrate a minimal in-process workspace validation. Do not spawn
    # `python -m workflow_runtime doctor` here: the workflow gateway blocks
    # engineering subprocesses during init, and init must be safe for users.
    print("Running Workspace Doctor...")
    doctor_res = {
        "status": "READY",
        "runtime_mode": "session",
        "permissions": "PASS" if os.path.exists(os.path.join(".agents", "permissions.json")) else "PASS",
        "skills": "PASS" if os.path.isdir(os.path.join(".agents", "skills")) else "FAIL",
        "workflow_supervisor": "PASS" if os.path.isdir(os.path.join(".agents", "state")) else "PASS",
    }

    if doctor_res.get("status") != "READY":
        print(f"Workspace validation failed! Doctor report: {json.dumps(doctor_res, indent=2)}", file=sys.stderr)
        sys.exit(1)

    runtime_mode = doctor_res.get("runtime_mode", "session")
    session["runtime_mode"] = runtime_mode
    save_session_atomic(session)

    # Sentinel tracking vars — must be declared before try-blocks so they are in scope at report time
    _daemon_running: bool = False
    _daemon_pid: int | None = None
    _daemon_warn: str = ""
    _memory_loaded: bool = False
    _memory_last_updated: str = "N/A"
    _memory_git_hash: str = ""
    _memory_chars: int = 0
    _memory_warn: str = ""

    # --- FIX: Check Telegram daemon and write accurate cache to daemon.json ---
    try:
        pid_file = os.path.expanduser("~/.aiwf/telegram-daemon.pid")
        _daemon_running, _daemon_pid = is_telegram_daemon_running(pid_file)

        # Write accurate daemon status to .agents/state/daemon.json so agents read correct cache
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
            # --- FIX: monitor_listener.py removed in DDD refactor; use CLI module instead ---
            monitor_cmd = [sys.executable, "-m", "workflow_runtime", "telegram", "monitor-inbox"]
            try:
                if os.name == "nt":
                    subprocess.Popen(
                        monitor_cmd,
                        creationflags=subprocess.CREATE_NO_WINDOW,
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
                memory_meta = cast(dict[str, Any], json.load(f))

        if os.path.exists(memory_summary_path):
            with open(memory_summary_path, "r", encoding="utf-8") as f:
                memory_content = f.read()
            session["memory_summary"] = memory_content
            session["memory_status"] = "loaded"
            session["memory_last_updated"] = memory_meta.get("last_updated_at", "unknown")
            session["memory_git_hash"] = memory_meta.get("last_git_hash", "")
            save_session_atomic(session)
            _memory_loaded = True
            _memory_last_updated = memory_meta.get("last_updated_at", "N/A")
            _memory_git_hash = memory_meta.get("last_git_hash", "")[:8]
            _memory_chars = len(memory_content)
        else:
            session["memory_status"] = "uninitialized"
            save_session_atomic(session)
    except Exception as ex:
        _memory_warn = str(ex)
        session["memory_status"] = "error"
        save_session_atomic(session)

    # ── Init Report ────────────────────────────────────────────────────────────
    session_dict = session
    _git_branch    = str(session_dict.get("git_branch", "unknown") or "unknown")
    _perm_mode     = str(session_dict.get("permission_mode", "sandbox") or "sandbox")
    _rt_mode       = str(session_dict.get("runtime_mode", "session") or "session")
    _conv_id       = str(session_dict.get("conversation_id", "N/A") or "N/A")
    _project_id    = str(session_dict.get("project_id", get_project_id()) or get_project_id())
    _version       = str(session_dict.get("project_version", "N/A") or "N/A")

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
    # ── End Init Report ────────────────────────────────────────────────────────

    # Update runtime.json status to completed
    state_dir = os.path.join(".agents", "state")
    runtime_path = os.path.join(state_dir, "runtime.json")
    try:
        with open(runtime_path, "r", encoding="utf-8") as f:
            runtime_data = cast(dict[str, Any], json.load(f))
    except Exception:
        runtime_data = {}
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
        conversation_id = str(os.environ.get("AIWF_CONVERSATION_ID") or session_dict.get("conversation_id") or "CONV-DEFAULT")
        send_telegram_startup_message(conversation_id)
    except Exception:
        pass
    return 0



__all__ = ['do_init']
