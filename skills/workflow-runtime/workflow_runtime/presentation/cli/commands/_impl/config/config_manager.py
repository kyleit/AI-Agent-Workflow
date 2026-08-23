from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, cast

import workflow_runtime.infrastructure.session.session as session_mod
from workflow_runtime.infrastructure.session.state_sync import (
    read_json_safe, write_json_atomic)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    ensure_project_registered_from_config, is_telegram_daemon_running)
from workflow_runtime.presentation.cli.commands._impl.system.runtime_bus import (
    start_runtime_bus_daemon)

RUNTIME_CMD_DIR = os.path.join(".agents", "runtime", "commands")


def do_config_action(args: argparse.Namespace) -> int:
    check_only = bool(getattr(args, "check_only", False))
    no_start = bool(getattr(args, "no_start", False))
    report: list[tuple[str, str, str]] = []

    if not check_only:
        os.makedirs(RUNTIME_CMD_DIR, exist_ok=True)
    report.append(("runtime_command_dir", "OK" if os.path.isdir(RUNTIME_CMD_DIR) else "MISSING", RUNTIME_CMD_DIR))

    try:
        init_fn: Any = getattr(session_mod, "refresh_initialize_dependencies", None)
        deps: dict[str, str] = cast(dict[str, str], init_fn()) if callable(init_fn) and not check_only else {"path": ".agents/state/runtime/dependencies.json"}
        deps_exists = os.path.exists(os.path.join(".agents", "state", "runtime", "dependencies.json"))
        report.append(("deps_cache", "OK" if deps_exists else "MISSING", str(deps.get("path", ""))))
    except Exception as e:
        report.append(("deps_cache", "ERROR", str(e)))

    try:
        git_cache_path = os.path.join(".agents", "state", "git.json")
        if check_only and not os.path.exists(git_cache_path):
            report.append(("git_read_cache", "MISSING", git_cache_path))
        else:
            refresh_git_fn: Any = getattr(session_mod, "refresh_git_state_cache", None)
            git_state = cast(dict[str, Any], refresh_git_fn()) if callable(refresh_git_fn) and not check_only else read_json_safe(git_cache_path)
            report.append(("git_read_cache", "OK" if git_state.get("ok", True) else "ERROR", str(git_state.get("branch", ""))))
    except Exception as e:
        report.append(("git_read_cache", "ERROR", str(e)))

    if not check_only:
        reg = ensure_project_registered_from_config()
        report.append(("project_registry", str(reg.get("status", "unknown")).upper(), str(reg.get("path") or reg.get("message") or "")))
    else:
        report.append(("project_registry", "SKIPPED", "check-only"))

    runtime_pid_file = os.path.expanduser("~/.aiwf/runtime.pid")
    runtime_running, runtime_pid = is_telegram_daemon_running(runtime_pid_file)
    if runtime_running:
        report.append(("runtime_daemon", "RUNNING", f"PID {runtime_pid}"))
    elif check_only or no_start:
        report.append(("runtime_daemon", "STOPPED", runtime_pid_file))
    else:
        started, pid, status = start_runtime_bus_daemon()
        report.append(("runtime_daemon", "STARTED" if started else status.upper(), f"PID {pid}"))

    try:
        import importlib
        _tn_mod = importlib.import_module('workflow_runtime.presentation.cli.commands._impl.ui.telegram_notify')
        telegram_token = bool(getattr(_tn_mod, 'has_global_telegram_token', lambda: False)())
    except Exception:
        telegram_token = bool(os.environ.get('TELEGRAM_BOT_TOKEN', ''))
    report.append(("telegram_token", "OK" if telegram_token else "MISSING", "~/.aiwf/.env.telegram-notify"))
    if telegram_token and runtime_running:
        report.append(("telegram_worker", "SUPERVISED", f"runtime PID {runtime_pid}"))
    elif telegram_token:
        report.append(("telegram_worker", "WAITING", "start runtime daemon to supervise Telegram"))
    else:
        report.append(("telegram_worker", "SKIPPED", "run `aiwf telegram config` first"))

    get_ctx_fn: Any = getattr(session_mod, "get_current_project_context", None)
    project_context: dict[str, Any] = cast(dict[str, Any], get_ctx_fn()) if callable(get_ctx_fn) else {}
    print("AIWF Configuration Check")
    print("========================")
    print(f"project: {project_context.get('name')} — {project_context.get('path')}")
    chat_id_val = project_context.get("telegram_chat_id")
    chat_str = f" — telegram_chat_id={chat_id_val}" if chat_id_val else ""
    print(f"project_registered: {'yes' if project_context.get('registered') else 'no'}{chat_str}")
    for name, status_val, detail in report:
        print(f"{name}: {status_val}" + (f" — {detail}" if detail else ""))
    nl = "\n"
    print(f"{nl}Agent-safe runtime command examples:")
    print("- deps.resolve: write .agents/runtime/commands/runtime.request.json with command='deps.resolve'")
    print("- git.status: write .agents/runtime/commands/runtime.request.json with command='git.status'")
    return 0


def do_permission(args: argparse.Namespace) -> int:
    from workflow_runtime.infrastructure.session.session import (
        get_project_permission_config_path, load_project_permissions,
        load_session, validate_permissions_data, write_project_permissions_atomic)

    subaction = getattr(args, "subaction", None)
    if subaction == "show":
        config = load_project_permissions()
        if not config:
            print("Error: permissions.json has not been initialized. Run 'init' subcommand first.", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return 0

    elif subaction == "validate":
        config = load_project_permissions()
        if not config:
            print("Error: permissions.json file does not exist.", file=sys.stderr)
            sys.exit(1)
        valid, msg = validate_permissions_data(config)
        if not valid:
            print(f"Validation failed: {msg}", file=sys.stderr)
            sys.exit(1)
        print("Validation succeeded: permissions.json is valid.")
        return 0

    elif subaction == "init":
        existing = load_project_permissions()
        if existing and not getattr(args, "force", False):
            print(f"Error: permissions.json already exists with mode '{existing.get('mode')}' at {get_project_permission_config_path()}.", file=sys.stderr)
            print("Use 'change' subcommand to modify permission mode or use '--force' to re-initialize.", file=sys.stderr)
            sys.exit(1)

        mode = str(getattr(args, "mode", None) or "")

        session = load_session()
        legacy_mode = str(session.get("permission_mode", ""))
        if not mode:
            if legacy_mode:
                mode = legacy_mode
                print(f"Migrating legacy permission mode '{legacy_mode}' from current session.")
            else:
                mode = "sandbox"
        else:
            if legacy_mode and legacy_mode != mode:
                print(f"Detected legacy permission mode '{legacy_mode}' in current session.")

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
        print(f"Successfully initialized project permission mode to '{mode}' at {get_project_permission_config_path()}.")
        return 0

    elif subaction == "change":
        existing = load_project_permissions()
        if not existing:
            print("Error: permissions.json has not been initialized. Run 'init' subcommand first.", file=sys.stderr)
            sys.exit(1)

        old_mode = str(existing.get("mode", ""))
        new_mode = str(getattr(args, "mode", "sandbox"))

        if old_mode == new_mode:
            print(f"Permission mode is already set to '{new_mode}'. No changes made.")
            return 0

        escalating = False
        if old_mode == "sandbox" and new_mode in ["full_access", "unrestricted"]:
            escalating = True
        elif old_mode == "full_access" and new_mode == "unrestricted":
            escalating = True

        if escalating and not getattr(args, "force", False):
            sys.stdout.write(f"WARNING: Escalating permission mode from '{old_mode}' to '{new_mode}'.\n")
            sys.stdout.write("This allows AI agents to execute code or write files with higher privileges.\n")
            sys.stdout.write("Are you sure you want to proceed? (y/N): ")
            sys.stdout.flush()
            try:
                response = sys.stdin.readline().strip().lower()
            except Exception:
                response = "n"
            if response not in ["y", "yes"]:
                print("Permission change aborted by user.")
                sys.exit(1)

        revision = int(existing.get("config_revision", 1)) + 1
        existing.update({
            "mode": new_mode,
            "config_revision": revision,
            "updated_at": datetime.now().astimezone().isoformat(),
            "updated_by": "user",
            "permissions": {
                "default_mode": new_mode,
                "autonomous_delivery": True if new_mode == "full_access" else False,
                "auto_continue_internal_phases": True if new_mode == "full_access" else False,
                "stop_at_release_approval": True,
                "require_separate_git_approval": True,
                "require_separate_release_approval": True,
                "require_separate_deploy_approval": True,
                "max_retries_per_task": 3,
                "max_replans_per_work_item": 2,
                "max_agent_reassignments_per_task": 2
            }
        })
        write_project_permissions_atomic(existing)
        print(f"Successfully changed project permission mode from '{old_mode}' to '{new_mode}'.")
        return 0

    get_mode_fn: Any = getattr(session_mod, "get_permission_mode", None)
    mode = str(get_mode_fn()) if callable(get_mode_fn) else "sandbox"
    print(f"Permission Mode: {mode}")
    print("\nStatus of common actions:")
    actions = [
        "normal_file_write",
        "source_code_change",
        "test_command",
        "build_command",
        "memory_update",
        "git_commit",
        "git_push",
        "git_tag",
        "git_merge",
        "release",
        "destructive_delete",
        "secret_change",
        "permission_mode_change"
    ]
    req_app_fn: Any = getattr(session_mod, "requires_approval", None)
    for action in actions:
        req = bool(req_app_fn(action)) if callable(req_app_fn) else True
        status = "REQUIRED_APPROVAL (Hard-gated)" if req else "ALLOWED (Bypass)"
        print(f"- {action}: {status}")
    return 0


def do_rules_action(args: Any) -> None:
    if (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "status":
        state_dir = os.path.join(".agents", "state")
        rules_file = os.path.join(state_dir, "rules.json")
        rules_data = read_json_safe(rules_file)
        raw_rules = rules_data.get("active_rules")
        if not rules_data or not raw_rules:
            rules_list: list[dict[str, str]] = []
            for r_path in ["AI_RULES.md", os.path.join(".agents", "AGENTS.md")]:
                if os.path.exists(r_path):
                    try:
                        with open(r_path, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        current_section = "General"
                        for line in lines:
                            if line.startswith("#"):
                                current_section = line.strip("# \n")
                            elif line.strip().startswith("-") or line.strip().startswith("*"):
                                rules_list.append({
                                    "rule_id": f"RULE-{len(rules_list)+1:03d}",
                                    "rule_text": line.strip("-* \n"),
                                    "source": f"{os.path.basename(r_path)} ({current_section})"
                                })
                    except Exception:
                        pass
            rules_data = {
                "active_rules": rules_list,
                "loaded_at": datetime.now().astimezone().isoformat()
            }
            write_json_atomic(rules_file, rules_data)
        print(json.dumps(rules_data, indent=2))


def do_registry(args: Any) -> None:
    from workflow_runtime.application.workflow import aiwf_registry
    sub = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    if sub == "register":
        res = aiwf_registry.register_project(
            args.path,
            force=args.force,
            source=args.source,
            framework_root=args.framework_root
        )
        if res.get("status") == "success":
            print("AIWF project registered successfully.")
            print(f"Project Path: {res.get('project_path')}")
            print(f"Registry Path: {res.get('registry_path')}")
        else:
            print(f"[ERROR] {res.get('message')}")
            sys.exit(1)
    elif sub == "unregister":
        target = args.path if args.path else "."
        success = bool(aiwf_registry.unregister_project(target))
        if success:
            print(f"Project unregistered successfully: {target}")
        else:
            print(f"Project not found in registry: {target}")
    elif sub == "list":
        projects = aiwf_registry.list_projects()
        if not projects:
            print("No projects registered yet.")
            return
        print(f"{'ID':<34} | {'Name':<20} | {'Status':<8} | {'Version':<8} | {'Path'}")
        print("-" * 100)
        for p in projects:
            p_id = str(p.get("id", ""))
            p_name = str(p.get("name", ""))[:20]
            p_status = str(p.get("status", ""))
            p_ver = str(p.get("aiwf_version", ""))
            p_path = str(p.get("path", ""))
            print(f"{p_id:<34} | {p_name:<20} | {p_status:<8} | {p_ver:<8} | {p_path}")
    elif sub == "doctor":
        report = aiwf_registry.doctor_registry()
        print(f"Registry Path: {report.get('registry_path')}")
        print(f"Total Registered: {report.get('total_registered')}")
        print(f"Active Projects: {report.get('active')}")
        print(f"Missing Projects: {report.get('missing')}")
        details = report.get("details", [])
        if details:
            print("\nDetails:")
            for d in details:
                name_str = str(d.get("name", ""))
                path_str = str(d.get("path", ""))
                status_str = f"[{str(d.get('status', '')).upper()}]"
                raw_issues = d.get("issues", [])
                issues_list = [str(x) for x in cast(list[Any], raw_issues)] if isinstance(raw_issues, list) else []
                issues_str = f" (Issues: {', '.join(issues_list)})" if issues_list else ""
                print(f"  - {name_str} ({path_str}) {status_str}{issues_str}")
    elif sub == "cleanup":
        res = aiwf_registry.cleanup_registry()
        tot_rem = res.get('total_removed')
        rem_act = res.get('remaining')
        print(f"Cleanup complete. Total Removed: {tot_rem}. Remaining active: {rem_act}.")
        rem_paths = res.get("removed_paths", [])
        if rem_paths:
            print("Removed paths:")
            for rp in rem_paths:
                print(f"  - {rp}")


__all__ = [
    "do_config_action",
    "do_permission",
    "do_rules_action",
    "do_registry",
]
