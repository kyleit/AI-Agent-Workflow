from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from workflow_runtime.application.analysis.fingerprint import     calculate_project_fingerprint
from workflow_runtime.infrastructure.persistence.lease import WorkflowLease
from workflow_runtime.infrastructure.session.session import (
    SessionLock, load_session, save_session_atomic)
from workflow_runtime.infrastructure.session.state_sync import     deconstruct_state
from workflow_runtime.shared.errors import (DomainException,
                                            ForbiddenAISourceError,
                                            InvalidResumeTokenError)
from workflow_runtime.shared.git_utils import get_version_info

RUNTIME_COMMAND_DIR = os.path.join(".agents", "runtime", "commands")


def _run_core_cli_handler(handler_name: str, args: argparse.Namespace) -> None:
    from workflow_runtime.presentation.cli import handlers as core_handlers

    handler: Any = getattr(core_handlers, handler_name)
    if callable(handler):
        res_code = handler(args)
        exit_code = int(str(res_code if res_code is not None else 0))
        if exit_code != 0:
            sys.exit(exit_code)


def extract_work_item_id_from_text(value: str) -> str:
    import re
    match = re.search(r"\b(?:FEAT|FIX|QUICK)-\d+\b", value or "")
    return match.group(0) if match else ""


def sync_blueprint_approval_metadata(
    blueprint_path: str,
    approved_at: str,
    approved_by: str = "user",
) -> str:
    """Persist approval metadata in the Blueprint and return its new SHA-256."""
    import hashlib

    path = Path(blueprint_path)
    content = path.read_text(encoding="utf-8")
    had_trailing_newline = content.endswith(("\n", "\r"))
    lines = content.splitlines()

    metadata = {
        "status": "APPROVED",
        "approved_at": approved_at,
        "approved_by": approved_by,
    }
    if lines and lines[0].strip() == "---":
        closing_index = next(
            (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
            -1,
        )
    else:
        closing_index = -1

    if closing_index < 0:
        lines = ["---", *[f"{key}: {value}" for key, value in metadata.items()], "---", *lines]
    else:
        frontmatter = lines[1:closing_index]
        seen: set[str] = set()
        for index, line in enumerate(frontmatter):
            key, separator, _value = line.partition(":")
            normalized_key = key.strip()
            if separator and normalized_key in metadata:
                frontmatter[index] = f"{normalized_key}: {metadata[normalized_key]}"
                seen.add(normalized_key)
        missing = [f"{key}: {value}" for key, value in metadata.items() if key not in seen]
        lines = [lines[0], *frontmatter, *missing, *lines[closing_index:]]

    updated = "\n".join(lines)
    if had_trailing_newline or not updated.endswith("\n"):
        updated += "\n"
    path.write_text(updated, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_bound_owner_blueprint_approval(work_item_id: str, blueprint_path: str) -> bool:
    """Accept approval only when a matching UI/bridge response exists."""
    runtime_dir = Path.cwd() / ".agents" / "runtime"
    expected_path = Path(blueprint_path).resolve()

    def _selected(value: Any) -> bool:
        return str(value or "").strip().lower() in {
            "approve", "approved", "continue", "proceed", "yes", "y", "true"
        }

    def _context_matches(context: Any) -> bool:
        if not isinstance(context, dict):
            return True
        context_work_item = str(
            context.get("work_item_id") or context.get("workflow_id") or ""
        )
        context_blueprint = str(context.get("blueprint") or "")
        if context_work_item and context_work_item != str(work_item_id):
            return False
        if context_blueprint and Path(context_blueprint).resolve() != expected_path:
            return False
        return True

    pending = _read_json_file(runtime_dir / "pending-choice.json")
    response = _read_json_file(runtime_dir / "choice-response.json")
    if (
        pending.get("id") == "blueprint_approval"
        and response.get("id") == "blueprint_approval"
        and _selected(response.get("selected_id") or response.get("selected"))
        and _context_matches(pending.get("context"))
    ):
        return True

    prompt_request = _read_json_file(runtime_dir / "prompt-request.json")
    prompt_response = _read_json_file(runtime_dir / "prompt-response.json")
    request_choice = str(prompt_request.get("choice_id") or "")
    response_choice = str(prompt_response.get("choice_id") or prompt_response.get("id") or "")
    if (
        request_choice == "blueprint_approval"
        and response_choice == request_choice
        and prompt_request.get("status") == "pending"
        and bool(prompt_request.get("approval_gate"))
        and _selected(
            prompt_response.get("selected_option")
            or prompt_response.get("selected")
            or prompt_response.get("response")
        )
    ):
        return True

    receipt = _read_json_file(runtime_dir / "owner-approval.json")
    return (
        receipt.get("choice_id") == "blueprint_approval"
        and receipt.get("work_item_id") == str(work_item_id)
        and Path(str(receipt.get("blueprint_path") or "")).resolve() == expected_path
        and _selected(receipt.get("selected_option"))
        and receipt.get("source") == "bound_prompt"
    )


def _read_json_file(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return cast(dict[str, Any], value) if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}


def get_current_project_context() -> dict[str, Any]:
    project_root = _resolve_aiwf_project_root()
    context: dict[str, Any] = {
        "name": os.path.basename(project_root),
        "path": ".",
        "absolute_path": project_root,
        "registered": False,
        "registry_id": None,
        "telegram_chat_id": None,
    }
    for manifest_path in (os.path.join(project_root, ".agents", "MANIFEST.json"), os.path.join(project_root, "MANIFEST.json")):
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                if isinstance(manifest, dict):
                    manifest_dict = cast(dict[str, Any], manifest)
                    context["name"] = str(manifest_dict.get("name") or context["name"])
                break
            except Exception:
                pass
    try:
        from workflow_runtime.application.workflow import aiwf_registry
        registry = aiwf_registry.load_registry()
        current = aiwf_registry.normalize_path(project_root)
        raw_projects = registry.get("projects", [])
        projects_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_projects) if isinstance(raw_projects, list) else []
        for project in projects_list:
            if aiwf_registry.normalize_path(str(project.get("path", "."))) == current:
                context["registered"] = True
                context["registry_id"] = project.get("id")
                context["telegram_chat_id"] = project.get("telegram_chat_id")
                context["registry_status"] = project.get("status")
                break
    except Exception as e:
        context["registry_error"] = str(e)
    return context


def _is_aiwf_project_root(path: str) -> bool:
    return os.path.exists(os.path.join(path, ".agents", "AI_RULES.md")) or os.path.exists(os.path.join(path, "AI_RULES.md"))


def _resolve_aiwf_project_root() -> str:
    cwd = os.path.abspath(".")
    if _is_aiwf_project_root(cwd):
        return cwd
    probe = Path(__file__).resolve()
    for parent in probe.parents:
        if parent.name == ".agents":
            return str(parent.parent)
        if parent.name == "public_export":
            return str(parent.parent)
        if _is_aiwf_project_root(str(parent)):
            return str(parent)
    try:
        from workflow_runtime.application.workflow import aiwf_registry
        registry = aiwf_registry.load_registry()
        raw_projects = registry.get("projects", [])
        projects_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_projects) if isinstance(raw_projects, list) else []
        for project in projects_list:
            path = str(project.get("path") or "")
            if path and os.path.exists(path) and _is_aiwf_project_root(path):
                return os.path.abspath(path)
    except Exception:
        pass
    return cwd


def sync_analysis_agents_to_session() -> None:
    session = load_session()
    analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data_dict = cast(dict[str, Any], data)
                session["analysis_agents"] = data_dict.get("agents", [])
            else:
                session["analysis_agents"] = []
        except Exception:
            session["analysis_agents"] = []
    else:
        session["analysis_agents"] = []
    save_session_atomic(session)


def is_telegram_daemon_running(pid_file: str) -> tuple[bool, int | None]:
    pid: int | None = None
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r", encoding="utf-8") as f:
                pid = int(f.read().strip())
            if os.name == "nt":
                if _is_outside_workflow_gateway():
                    return False, pid
                import subprocess
                try:
                    res = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    return (str(pid) in res.stdout), pid
                except PermissionError:
                    return False, pid
            os.kill(pid, 0)
            return True, pid
        except Exception:
            return False, pid
    return False, None


def _state_write_json(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp_path, path)


def runtime_bus_autostart_target() -> str:
    import platform
    system = platform.system()
    if system == "Darwin":
        return os.path.expanduser("~/Library/LaunchAgents/net.aiwf.runtime.plist")
    if system == "Windows":
        return "AIWF Runtime Daemon"
    return os.path.expanduser("~/.config/systemd/user/aiwf-runtime.service")


def runtime_bus_startup_folder_target() -> str:
    startup = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")),
        "Microsoft",
        "Windows",
        "Start Menu",
        "Programs",
        "Startup",
    )
    return os.path.join(startup, "AIWF Runtime Daemon.cmd")


def _is_gateway_block_exception(exc: BaseException) -> bool:
    return "EXECUTION_BLOCKED" in str(exc)


def _is_outside_workflow_gateway() -> bool:
    session_data: dict[str, Any] = {}
    session_path = os.path.abspath(os.path.join(".", ".agents", ".session.json"))
    if os.path.exists(session_path):
        try:
            with open(session_path, "r", encoding="utf-8") as f:
                raw_sd = json.load(f)
                if isinstance(raw_sd, dict):
                    session_data = cast(dict[str, Any], raw_sd)
        except Exception:
            session_data = {}
    execution_mode = str(os.environ.get("AIWF_EXECUTION_MODE") or session_data.get("execution_mode") or "")
    workflow_id = str(os.environ.get("AIWF_WORKFLOW_ID") or session_data.get("workflow_id") or "")
    return execution_mode != "workflow" or not workflow_id


def ensure_project_registered_from_config() -> dict[str, Any]:
    try:
        from workflow_runtime.application.workflow import aiwf_registry
        registry = aiwf_registry.load_registry()
        current = str(aiwf_registry.normalize_path("."))
        raw_projects = registry.get("projects", [])
        projects_list: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_projects) if isinstance(raw_projects, list) else []
        for project in projects_list:
            if str(aiwf_registry.normalize_path(str(project.get("path", "")))) == current:
                return {"status": "already_registered", "path": current}
        result = aiwf_registry.register_project(".", force=True, source="config")
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


class RuntimeInputGate:
    @staticmethod
    def enter_waiting_state(prompt_id: str, question: str, options: list[Any]) -> dict[str, Any]:
        import secrets
        from datetime import datetime
        token = secrets.token_hex(16)
        pending: dict[str, Any] = {
            "input_id": prompt_id,
            "question": question,
            "options": options,
            "resume_token": token,
            "created_at": datetime.now().astimezone().isoformat()
        }

        session = load_session()
        session["status"] = "waiting_input"
        session["pending_input"] = pending

        log_line = f"> Runtime waiting for input on prompt '{prompt_id}'. Secure token generated."
        if "current_logs" in session:
            raw_logs = session["current_logs"]
            logs_list: list[Any] = cast(list[Any], raw_logs) if isinstance(raw_logs, list) else []
            logs_list.append(log_line)
            session["current_logs"] = logs_list
        else:
            session["current_logs"] = [log_line]

        save_session_atomic(session)
        return pending

    @staticmethod
    def submit_input(prompt_id: str, value: str, source: str, token: str) -> bool:
        if source and source.lower() == "ai":
            raise ForbiddenAISourceError("Input submission from AI sources is strictly forbidden.")

        session = load_session()
        raw_pending = session.get("pending_input")
        if not isinstance(raw_pending, dict):
            print("No pending input waiting in session.")
            return False

        pending = cast(dict[str, Any], raw_pending)
        if pending.get("input_id") != prompt_id:
            print(f"Prompt ID mismatch: expected {pending.get('input_id')}, got {prompt_id}.")
            return False

        if pending.get("resume_token") != token:
            raise InvalidResumeTokenError("Security token mismatch. Access denied.")

        session["status"] = "completed"
        session["pending_input"] = None

        log_line = f"> Input for prompt '{prompt_id}' accepted from source '{source}'."
        if "current_logs" in session:
            raw_logs = session["current_logs"]
            logs_list: list[Any] = cast(list[Any], raw_logs) if isinstance(raw_logs, list) else []
            logs_list.append(log_line)
            session["current_logs"] = logs_list

        save_session_atomic(session)
        return True


__all__ = [
    "DomainException",
    "ForbiddenAISourceError",
    "InvalidResumeTokenError",
    "SessionLock",
    "WorkflowLease",
    "calculate_project_fingerprint",
    "deconstruct_state",
    "extract_work_item_id_from_text",
    "get_current_project_context",
    "get_version_info",
    "is_telegram_daemon_running",
    "sync_analysis_agents_to_session",
    "ensure_project_registered_from_config",
    "RuntimeInputGate",
    "_run_core_cli_handler",
    "_state_write_json",
    "_is_gateway_block_exception",
    "runtime_bus_autostart_target",
    "runtime_bus_startup_folder_target",
]
