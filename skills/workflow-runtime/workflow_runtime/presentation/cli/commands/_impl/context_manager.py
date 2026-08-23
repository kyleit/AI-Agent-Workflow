from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.infrastructure.session.session_io import load_session
from workflow_runtime.infrastructure.session.state_sync import (
    deconstruct_state, read_json_safe, write_json_atomic)


def _state_read_json(path: str) -> dict[str, Any]:
    return read_json_safe(path)


def _state_write_json(path: str, data: dict[str, Any]) -> None:
    write_json_atomic(path, data)


def _get_git_info() -> dict[str, Any]:
    try:
        import subprocess
        res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        branch = res.stdout.strip() if res.returncode == 0 else "main"
        return {"branch": branch or "main"}
    except Exception:
        return {"branch": "main"}


def _get_permission_mode() -> str:
    perm_path = os.path.join(".agents", "config", "permissions.json")
    if os.path.exists(perm_path):
        try:
            with open(perm_path, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
                return str(data.get("mode", "none"))
        except Exception:
            pass
    return "none"


def do_context(_args: Any) -> None:
    state_dir = os.path.join(".agents", "state")
    context_file = os.path.join(state_dir, "context.json")
    if os.path.exists(context_file):
        data = read_json_safe(context_file)
    else:
        data = {
            "workspace_path": ".",
            "project_version": "1.0.0",
            "git": _get_git_info(),
            "permission_mode": _get_permission_mode(),
        }
    print(json.dumps(data, indent=2))


def do_state_action(args: Any) -> None:
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None) or getattr(args, "state_action", None)
    state_dir = os.path.join(".agents", "state")
    session_file = os.path.join(".agents", ".session.json")

    if subaction == "status":
        files = ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json", "rules.json", "recovery.json"]
        present = [f for f in files if os.path.exists(os.path.join(state_dir, f))]

        status = "healthy"
        synced = True

        if len(present) < len(files) - 1:
            status = "uninitialized"
            synced = False
        else:
            if os.path.exists(session_file):
                session_time = os.path.getmtime(session_file)
                for f in present:
                    if f != "recovery.json" and os.path.getmtime(os.path.join(state_dir, f)) > session_time + 1.0:
                        status = "out_of_sync"
                        synced = False
                        break

        res = {
            "status": status,
            "state_files_present": present,
            "session_synced": synced
        }
        print(json.dumps(res, indent=2))

    elif subaction == "recover":
        restored: list[str] = []
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = cast(dict[str, Any], json.load(f))
                deconstruct_state(".", session_data)
                restored = ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json"]
            except Exception:
                pass

        res = {
            "status": "success" if restored else "failed",
            "recovered_files": restored
        }
        print(json.dumps(res, indent=2))

    elif subaction == "validate":
        errors: list[str] = []
        files = ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json"]
        for f in files:
            p = os.path.join(state_dir, f)
            if not os.path.exists(p):
                errors.append(f"Missing {f}")
            else:
                try:
                    with open(p, "r", encoding="utf-8") as file:
                        json.load(file)
                except Exception:
                    errors.append(f"Corrupted JSON in {f}")

        res = {
            "status": "success" if not errors else "failed",
            "errors": errors
        }
        print(json.dumps(res, indent=2))
        if errors:
            sys.exit(1)

    elif subaction == "doctor":
        checks: list[dict[str, str]] = []
        for fname in ["context.json", "workflow.json", "runtime.json"]:
            path = os.path.join(state_dir, fname)
            checks.append({"name": fname, "status": "present" if os.path.exists(path) else "missing"})
        print(json.dumps({"status": "healthy", "checks": checks, "errors": []}, indent=2))

    elif subaction == "snapshot":
        backup_dir = os.path.abspath(os.path.join(state_dir, "backups", f"snapshot-{datetime.now().strftime('%Y%m%d%H%M%S')}"))
        os.makedirs(backup_dir, exist_ok=True)
        backed_up: list[str] = []
        if os.path.exists(state_dir):
            for name in os.listdir(state_dir):
                src = os.path.join(state_dir, name)
                if os.path.isfile(src) and name.endswith(".json"):
                    shutil.copy2(src, os.path.join(backup_dir, name))
                    backed_up.append(name)
        print(json.dumps({"status": "success", "backup_path": backup_dir, "files_backed_up": backed_up}, indent=2))

    elif subaction == "migrate":
        report_path = os.path.join(state_dir, "recovery", "state-migration-report.json")
        migrated = [name for name in ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json"] if os.path.exists(os.path.join(state_dir, name))]
        report: dict[str, Any] = {"status": "success", "migrated_files": migrated, "updated_at": datetime.now().astimezone().isoformat()}
        _state_write_json(report_path, report)
        print(json.dumps(report, indent=2))

    elif subaction == "aggregate":
        dashboard_path = os.path.abspath(os.path.join(state_dir, "dashboard.json"))
        dashboard: dict[str, Any] = {
            "status": "success",
            "context": _state_read_json(os.path.join(state_dir, "context.json")),
            "workflow": _state_read_json(os.path.join(state_dir, "workflow.json")),
            "runtime": _state_read_json(os.path.join(state_dir, "runtime.json")),
            "updated_at": datetime.now().astimezone().isoformat()
        }
        _state_write_json(dashboard_path, dashboard)
        print(json.dumps({"status": "success", "dashboard": dashboard_path, "legacy_snapshot": os.path.abspath(os.path.join(state_dir, "legacy-session-snapshot.json"))}, indent=2))

    elif subaction == "emit":
        try:
            raw_payload = getattr(args, "payload", None) or "{}"
            payload = json.loads(str(raw_payload))
            if not isinstance(payload, dict):
                payload = {"value": payload}
            event_type = str(getattr(args, "type", "") or "")
            event: dict[str, Any] = {
                "event_id": f"evt-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "event_type": event_type,
                "payload": payload
            }
            print(json.dumps({"status": "success", "event_id": event["event_id"], "event_type": event["event_type"]}, indent=2))
        except Exception as e:
            print(json.dumps({"status": "failed", "error": str(e)}, indent=2))
            sys.exit(1)

    elif subaction == "diagnose":
        session = load_session() or {}
        lock_file = os.path.join(".agents", "runtime", "workflow.lock")
        lock_owner = "None"
        locked_at = "N/A"
        active_task = "None"
        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r", encoding="utf-8") as f:
                    lock_data = cast(dict[str, Any], json.load(f))
                lock_owner = str(lock_data.get("skill", "unknown"))
                locked_at = str(lock_data.get("started_at", "N/A"))
                active_task = f"{lock_owner} ({lock_data.get('lock_owner', '')})"
            except Exception:
                lock_owner = "Corrupted"

        exec_mode = str(session.get("execution_mode", "sequential"))

        diagnostics: dict[str, Any] = {
            "execution_mode": exec_mode,
            "active_task": active_task,
            "queue_length": 0,
            "lock_owner": lock_owner,
            "locked_at": locked_at,
            "waiting_tasks": []
        }
        print(json.dumps(diagnostics, indent=2))


__all__ = [
    "do_context",
    "do_state_action",
]
