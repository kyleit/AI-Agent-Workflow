"""
workflow_runtime/presentation/cli/session_command_handlers.py

CLI command handlers for AIWF session lifecycle, prompts, and mail services.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any, cast


def handle_session(args: argparse.Namespace) -> int:
    import json
    from pathlib import Path

    from workflow_runtime.infrastructure.session.session_store import (
        SessionStore)
    store = SessionStore()
    sub = getattr(args, "subcommand", None)

    if sub == "read":
        data = store.load()
        key_val = getattr(args, "key", None)
        if key_val:
            val = data.get(str(key_val))
            print(json.dumps(val, indent=2, ensure_ascii=False) if val is not None else f"Key '{key_val}' not found.")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return 0

    elif sub == "reset":
        session_path = Path(store.get_path())
        if session_path.exists():
            session_path.unlink()
            print("Session reset.")
        else:
            print("No session file found.")
        return 0

    elif sub == "lock-status":
        lock_path = Path(store.get_path()).with_suffix(".lock")
        if lock_path.exists():
            print(f"Session is LOCKED: {lock_path}")
        else:
            print("Session is NOT locked.")
        return 0

    return 0


def handle_start(args: argparse.Namespace) -> int:
    """Start a skill execution and transition session to in_progress."""
    from workflow_runtime.presentation.cli.commands._impl.session.session_lifecycle import (
        do_start)
    return do_start(args)


def handle_step(args: argparse.Namespace) -> int:
    """Record a progress step into the current session log."""
    from workflow_runtime.presentation.cli.commands._impl.session.session_lifecycle import (
        do_step)
    return do_step(args)


def handle_complete(args: argparse.Namespace) -> int:
    """Mark current skill as completed and propose next step."""
    from workflow_runtime.presentation.cli.commands._impl.session.session_lifecycle import (
        do_complete)
    return do_complete(args)


def handle_fail(args: argparse.Namespace) -> int:
    """Mark current skill as failed and log the error reason."""
    from workflow_runtime.presentation.cli.commands._impl.session.session_lifecycle import (
        do_fail)
    return do_fail(args)


def handle_heartbeat(args: argparse.Namespace) -> int:
    """Print the current workflow state heartbeat box."""
    from workflow_runtime.presentation.cli.commands._impl.session.session_lifecycle import (
        do_heartbeat)
    return do_heartbeat(args)


def handle_prompt(args: argparse.Namespace) -> int:
    """Present an interactive prompt question and wait for user selection."""
    from workflow_runtime.presentation.cli.commands._impl.ui.ui_prompts import (
        do_prompt)
    return do_prompt(args)


def handle_mail(args: argparse.Namespace) -> int:
    """Handle the mail subcommand."""
    import json

    from workflow_runtime.application.session.mail_service import MailService

    svc = MailService()
    subaction = getattr(args, "subaction", None)

    if subaction == "register":
        try:
            info = svc.register()
            print(json.dumps({"status": "success", "session_id": info.get("session_id"), "session_name": info.get("session_name")}))
            return 0
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
            return 1

    elif subaction == "list":
        sessions = svc.list_sessions()
        print(json.dumps({"active_sessions": sessions}))
        return 0

    elif subaction == "send":
        to_name = getattr(args, "to", None)
        message = getattr(args, "message", None)
        if not to_name or not message:
            print(json.dumps({"status": "error", "message": "--to and --message are required for send"}))
            return 1
        success = svc.send(str(to_name), str(message))
        if success:
            print(json.dumps({"status": "success", "message": f"Mail sent to {to_name}"}))
            return 0
        else:
            print(json.dumps({"status": "error", "message": f"Failed to send mail to {to_name}"}))
            return 1

    elif subaction == "read":
        fn: Any = getattr(svc, "read", None)
        raw_mail: Any = fn() if callable(fn) else []
        mail = cast(list[dict[str, Any]], raw_mail) if isinstance(raw_mail, list) else []
        print(json.dumps({"mail": mail}, indent=2))
        return 0

    else:
        print(f"Unknown mail subaction: {subaction}")
        return 2


__all__ = [
    "handle_session",
    "handle_prompt",
    "handle_mail",
    "handle_init",
    "handle_runbook",
    "handle_heartbeat",
]
