# common.py
from __future__ import annotations

import os
from typing import Any, cast


def log_info(msg: str) -> None:
    print(f"\033[1;34m[INFO]\033[0m {msg}", flush=True)


def log_success(msg: str) -> None:
    print(f"\033[1;32m[SUCCESS]\033[0m {msg}", flush=True)


def log_warn(msg: str) -> None:
    print(f"\033[1;33m[WARN]\033[0m {msg}", flush=True)


def log_error(msg: str) -> None:
    print(f"\033[1;31m[ERROR]\033[0m {msg}", flush=True)


def get_project_root() -> str:
    return os.getcwd()


def to_posix_path(path_str: str) -> str:
    """Chuẩn hóa đường dẫn về dạng POSIX với ký tự '/' (tránh lỗi Windows path trong metadata)."""
    return path_str.replace("\\", "/")


def integrate_runtime_api() -> bool:
    """No-op: kept for backward compat. Package imports are now used directly."""
    return True


def session_start(skill: str, command: str, checkpoint: int, step: str) -> None:
    try:
        from workflow_runtime.infrastructure.session.session_io import (
            load_session, save_session_atomic)
        from workflow_runtime.presentation.cli.workflow_runtime_shared import (
            update_context_health)

        raw_session: Any = load_session()
        session: dict[str, Any] = dict(cast(dict[str, Any], raw_session)) if isinstance(raw_session, dict) else {}
        if not session:
            session = {"workspace": {"path": ".", "valid": True}}

        active_skill = session.get("current_skill")
        if active_skill and active_skill != skill:
            log_info(f"Skipping session start for '{skill}' because active skill is '{active_skill}'.")
            return

        session["status"] = "in_progress"
        session["checkpoint"] = checkpoint
        session["current_skill"] = skill
        session["current_command"] = command
        session["current_step"] = step
        session["current_logs"] = [f"> Starting {skill}..."]
        update_context_health(session)
        save_session_atomic(session)
        log_info(f"Session updated: {skill} start.")
    except Exception as e:
        log_warn(f"Failed to call runtime start API: {e}")


def session_step(step: str, log_msg: str) -> None:
    try:
        from workflow_runtime.infrastructure.session.session_io import (
            load_session, save_session_atomic)
        from workflow_runtime.presentation.cli.workflow_runtime_shared import (
            update_context_health)

        raw_session: Any = load_session()
        session: dict[str, Any] = dict(cast(dict[str, Any], raw_session)) if isinstance(raw_session, dict) else {}
        if session:
            active_skill = session.get("current_skill")
            if active_skill and active_skill not in ["project-memory-update", "project-memory-bootstrap"]:
                return

            session["current_step"] = step
            raw_logs = session.get("current_logs")
            logs_list = cast(list[Any], raw_logs) if isinstance(raw_logs, list) else []
            if log_msg:
                logs_list.append(log_msg)
            session["current_logs"] = logs_list
            update_context_health(session)
            save_session_atomic(session)
    except Exception as e:
        log_warn(f"Failed to call runtime step API: {e}")


def session_complete(checkpoint: int, step: str, next_skill: str, next_cmd: str) -> None:
    try:
        from workflow_runtime.infrastructure.session.session_io import (
            load_session, save_session_atomic)
        from workflow_runtime.presentation.cli.workflow_runtime_shared import (
            update_context_health)

        raw_session: Any = load_session()
        session: dict[str, Any] = dict(cast(dict[str, Any], raw_session)) if isinstance(raw_session, dict) else {}
        if session:
            active_skill = session.get("current_skill")
            if active_skill and active_skill not in ["project-memory-update", "project-memory-bootstrap"]:
                update_context_health(session)
                save_session_atomic(session)
                log_info("Skipped workflow routing update of session, but updated context health successfully.")
                return

            session["status"] = "completed"
            session["checkpoint"] = checkpoint
            session["current_step"] = step
            raw_logs = session.get("current_logs")
            logs_list = cast(list[Any], raw_logs) if isinstance(raw_logs, list) else []
            logs_list.append("> Completed successfully.")
            session["current_logs"] = logs_list
            session["suggested_next_skill"] = next_skill
            session["suggested_next_command"] = next_cmd
            update_context_health(session)
            save_session_atomic(session)
            log_success(f"Session completed: checkpoint {checkpoint} reached.")
    except Exception as e:
        log_warn(f"Failed to call runtime complete API: {e}")


def session_fail(step: str, log_msg: str) -> None:
    try:
        from workflow_runtime.infrastructure.session.session_io import (
            load_session, save_session_atomic)
        from workflow_runtime.presentation.cli.workflow_runtime_shared import (
            update_context_health)

        raw_session: Any = load_session()
        session: dict[str, Any] = dict(cast(dict[str, Any], raw_session)) if isinstance(raw_session, dict) else {}
        if session:
            active_skill = session.get("current_skill")
            if active_skill and active_skill not in ["project-memory-update", "project-memory-bootstrap"]:
                return

            session["status"] = "failed"
            session["current_step"] = step
            raw_logs = session.get("current_logs")
            logs_list = cast(list[Any], raw_logs) if isinstance(raw_logs, list) else []
            logs_list.append(f"Error: {log_msg}")
            session["current_logs"] = logs_list
            update_context_health(session)
            save_session_atomic(session)
    except Exception as e:
        log_warn(f"Failed to call runtime fail API: {e}")


__all__ = [
    "log_info",
    "log_success",
    "log_warn",
    "log_error",
    "get_project_root",
    "to_posix_path",
    "integrate_runtime_api",
    "session_start",
    "session_step",
    "session_complete",
    "session_fail",
]
