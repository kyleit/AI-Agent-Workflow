# workflow_runtime.py
# QUICK-038: Block direct file execution -- guard must be first
import sys as _sys
from typing import Any, cast

if _sys.argv[0].endswith("workflow_runtime.py") and __name__ == "__main__":
    _sys.stderr.write(
        "ERROR: Do not run this module file directly.\n"
        "Use: python -m workflow_runtime <subcommand> [args]\n"
    )
    _sys.exit(127)

import sys

if sys.version_info < (3, 11):
    sys.exit("Error: AIWF requires Python 3.11 or newer.")

import json
import os

# Add the directory containing this script to sys.path to resolve sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from workflow_runtime.application.verification.test_enforcer import \
    patch_subprocess

patch_subprocess()

if sys.version_info < (3, 11):
    print("Error: Python 3.11 or higher is required.", file=sys.stderr)
    sys.exit(1)

import atexit
import signal

from workflow_runtime.application.analysis.fingerprint import \
    calculate_project_fingerprint
from workflow_runtime.application.analytics.usage_sync_service import \
    sync_request_history
from workflow_runtime.domain.core.context_usage import estimate_context_usage
from workflow_runtime.infrastructure.events.heartbeat import print_heartbeat
from workflow_runtime.infrastructure.filesystem.atomic_writer import (
    read_json_safe, write_json_atomic)
from workflow_runtime.infrastructure.persistence.checkpoint import (
    get_checkpoint_name, validate_checkpoint_level)
from workflow_runtime.infrastructure.persistence.metadata_insight_records import (
    get_global_summary, get_project_summary, get_workflow_summary,
    save_usage_to_dbs)
from workflow_runtime.infrastructure.persistence.lease import WorkflowLease
from workflow_runtime.infrastructure.session.session import (
    load_session, save_session_atomic)
from workflow_runtime.infrastructure.session.session_lock import SessionLock
from workflow_runtime.infrastructure.session.state_sync import (
    aggregate_state, deconstruct_state)
from workflow_runtime.shared.drift import check_context_drift
from workflow_runtime.shared.git_utils import get_git_info, get_version_info
from workflow_runtime.shared.utils import get_memory_info, get_rag_info

__all__ = [
    "get_global_summary",
    "get_project_summary",
    "get_workflow_summary",
    "save_usage_to_dbs",
    "WorkflowLease",
    "load_session",
    "save_session_atomic",
    "check_context_drift",
    "get_git_info",
    "get_version_info",
    "get_memory_info",
    "get_rag_info",
    "get_checkpoint_name",
    "validate_checkpoint_level",
    "print_heartbeat",
    "read_json_safe",
    "write_json_atomic",
    "sync_request_history",
    "deconstruct_state",
    "estimate_context_usage",
    "SessionLock",
    "aggregate_state",
    "calculate_project_fingerprint",
    "cleanup_lease",
    "handle_sigterm",
]


def cleanup_lease():
    try:
        WorkflowLease.release()
    except Exception:
        pass


atexit.register(cleanup_lease)


def handle_sigterm(signum: Any, frame: Any):
    cleanup_lease()
    sys.exit(0)


try:
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)
except ValueError:
    # Under some testing environments, registering signal handlers on non-main threads fails
    pass


def get_project_id() -> str:
    path = os.path.join(".agents", "memory.config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("project_id", "ai-skill-framework")
        except Exception:
            pass
    return "ai-skill-framework"


def get_permission_mode() -> str:
    session = load_session()
    mode = session.get("permission_mode", "sandbox")
    if mode not in ["sandbox", "full_access", "unrestricted"]:
        return "sandbox"
    return str(mode)


from workflow_runtime.shared.errors import (ForbiddenAISourceError,
                                            InvalidResumeTokenError)


class RuntimeInputGate:
    @staticmethod
    def enter_waiting_state(prompt_id: str, question: str, options: list[Any]) -> dict[str, Any]:
        import secrets
        from datetime import datetime

        token = secrets.token_hex(16)
        pending = {
            "input_id": prompt_id,
            "question": question,
            "options": options,
            "resume_token": token,
            "created_at": datetime.now().astimezone().isoformat(),
        }

        session = load_session()
        session["status"] = "waiting_input"
        session["pending_input"] = pending

        log_line = f"> Runtime waiting for input on prompt '{prompt_id}'. Secure token generated."
        if "current_logs" in session:
            session["current_logs"].append(log_line)
        else:
            session["current_logs"] = [log_line]

        save_session_atomic(session)
        return pending

    @staticmethod
    def submit_input(prompt_id: str, value: str, source: str, token: str) -> bool:
        if source and source.lower() == "ai":
            raise ForbiddenAISourceError(
                "Input submission from AI sources is strictly forbidden."
            )

        session = load_session()
        pending = session.get("pending_input")
        if not pending:
            print("No pending input waiting in session.")
            return False

        if pending.get("input_id") != prompt_id:
            print(
                f"Prompt ID mismatch: expected {pending.get('input_id')}, got {prompt_id}."
            )
            return False

        if pending.get("resume_token") != token:
            raise InvalidResumeTokenError("Security token mismatch. Access denied.")

        session["status"] = "completed"
        session["pending_input"] = None

        log_line = f"> Input for prompt '{prompt_id}' accepted from source '{source}'."
        if "current_logs" in session:
            session["current_logs"].append(log_line)

        save_session_atomic(session)
        return True


def requires_approval(action_type: str, path: str | None = None) -> bool:
    mode = get_permission_mode()
    if mode == "unrestricted":
        return False

    session = load_session()
    is_autonomous = session.get("autonomous_delivery", False)

    # Hard-gated actions that ALWAYS require approval in full_access mode or autonomous mode
    release_actions = [
        "git_commit",
        "git_merge",
        "git_rebase",
        "git_tag",
        "git_push",
        "release",
        "publish",
        "deploy",
        "production_migration",
        "destructive_delete",
        "secret_rotation",
        "global_policy_modification",
        "permission_mode_change",
    ]
    if action_type in release_actions:
        from workflow_runtime.shared.utils import log_gate_resolution_event

        log_gate_resolution_event(
            f"Action: {action_type}", "BLOCKED_BY_RELEASE_BOUNDARY", "Blocked"
        )
        return True

    # Scope Protection Check
    auth: dict[str, Any] = cast(dict[str, Any], session.get("authorization", {})) if isinstance(session.get("authorization"), dict) else {}
    active_wi = os.environ.get("AIWF_ACTIVE_WORK_ITEM") or os.environ.get(
        "AIWF_WORK_ITEM_ID"
    )

    if active_wi and auth.get("work_item_id") and auth.get("work_item_id") != active_wi:
        from workflow_runtime.shared.utils import log_gate_resolution_event

        log_gate_resolution_event(
            f"Action: {action_type} for work item {active_wi}",
            "OUT_OF_SCOPE",
            "Blocked",
        )
        return True

    # Path boundary check
    if path:
        abs_path = os.path.abspath(path)
        cwd = os.path.abspath(os.getcwd())
        if not abs_path.startswith(cwd):
            from workflow_runtime.shared.utils import log_gate_resolution_event

            log_gate_resolution_event(
                f"Write to path: {path}", "OUT_OF_SCOPE", "Blocked"
            )
            return True

        basename = os.path.basename(abs_path)
        if basename in ["AI_RULES.md", "AGENTS.md"]:
            from workflow_runtime.shared.utils import log_gate_resolution_event

            log_gate_resolution_event(
                f"Modify policy file: {path}", "BLOCKED_BY_RELEASE_BOUNDARY", "Blocked"
            )
            return True

    if is_autonomous:
        # Bypass other approvals in autonomous mode
        return False

    if mode == "sandbox":
        return True

    from workflow_runtime.shared.utils import log_gate_resolution_event

    log_gate_resolution_event(
        f"Action: {action_type}", "AUTHORIZED_BY_FULL_ACCESS", "Allowed"
    )
    return False


def update_context_health(session: dict[str, Any]) -> None:
    # Auto-detect and sync current conversation_id and context usage
    from workflow_runtime.domain.core.context import \
        refresh_context_usage_for_active_conversation

    usage = refresh_context_usage_for_active_conversation(session)

    if "suggestion_gate" not in session:
        session["suggestion_gate"] = {
            "active": False,
            "raw_request": "",
            "classification": "",
            "recommended_skill": "",
            "options": [],
            "status": "idle",
        }

    # Sync current system status to prevent false drift detection
    session["git"] = get_git_info()
    session["version"] = get_version_info()
    session["memory"] = get_memory_info()
    session["rag"] = get_rag_info()

    # Inject Resident Orchestrator and Runtime Manager status details for Visualizer
    session["orchestrator_status"] = "DISABLED"
    session["runtime_manager_status"] = "DISABLED"
    session["orchestrator_pid"] = "N/A"
    session["orchestrator_id"] = "main-orchestrator"
    session["attach_mode"] = "N/A"
    session["last_heartbeat"] = "N/A"

    # 2. Save it to DBs if conversation_id exists
    conv_id = session.get("conversation_id")
    if conv_id:
        proj_id = get_project_id()
        skill = session.get("current_skill", "unknown")
        cmd = session.get("current_command", "unknown")
        try:
            save_usage_to_dbs(conv_id, proj_id, skill, cmd, usage)
        except Exception as e:
            print(f"Warning: could not save usage to DB: {e}", file=sys.stderr)
        try:
            from workflow_runtime.application.analytics.usage_sync_service import \
                sync_request_history

            sync_request_history(conv_id, proj_id, session=session)
        except Exception as e:
            print(f"Warning: could not sync request history: {e}", file=sys.stderr)

    # 3. Retrieve summaries from DBs
    wf_summary = get_workflow_summary(
        conv_id or "", usage.get("provider", "estimate"), usage.get("model", "auto")
    )
    if wf_summary.get("total_tokens", 0) == 0 and usage.get("total_tokens", 0) > 0:
        session["workflow_usage_summary"] = usage
    else:
        session["workflow_usage_summary"] = wf_summary

    session["project_usage_summary"] = get_project_summary(get_project_id())
    session["global_usage_summary"] = get_global_summary()

    try:
        from workflow_runtime.infrastructure.session.session_lock import \
            load_workflow_config

        config = load_workflow_config()
    except Exception:
        config = {}
    session["telemetry_config"] = config.get(
        "telemetry",
        {
            "context_thresholds": {"warning": 60, "high": 80, "critical": 95},
            "context_styles": {
                "healthy": {
                    "color": "#10b981",
                    "bg": "rgba(16, 185, 129, 0.1)",
                    "border": "rgba(16, 185, 129, 0.3)",
                    "icon": "🟢",
                    "label": "Healthy",
                },
                "warning": {
                    "color": "#f59e0b",
                    "bg": "rgba(245, 158, 11, 0.1)",
                    "border": "rgba(245, 158, 11, 0.3)",
                    "icon": "🟡",
                    "label": "Warning",
                },
                "high": {
                    "color": "#f97316",
                    "bg": "rgba(249, 115, 22, 0.1)",
                    "border": "rgba(249, 115, 22, 0.3)",
                    "icon": "🟠",
                    "label": "High",
                },
                "critical": {
                    "color": "#ef4444",
                    "bg": "rgba(239, 68, 68, 0.1)",
                    "border": "rgba(239, 68, 68, 0.3)",
                    "icon": "🔴",
                    "label": "Critical",
                },
            },
            "cost_thresholds": {"warning_usd": 10.0, "critical_usd": 50.0},
        },
    )

    # 4. Populate backward-compatible context_usage object
    session["context_usage"] = {
        "total_tokens": usage.get("active_tokens", 0),
        "limit_tokens": usage.get("limit_tokens", 2000000),
        "percentage": usage.get("percentage", 0.0),
    }

    # 5. Check drift
    drifted, _msg = check_context_drift(session)
    session["context_health"] = "broken" if drifted else "healthy"

    # 6. Generate Context Breakdown state
    try:
        from workflow_runtime.application.analysis.breakdown_engine import \
            update_breakdown_file

        update_breakdown_file(session, ".")
    except Exception:
        pass

# --- Re-export for backward compatibility ---
from workflow_runtime.presentation.cli.telegram_notifier import (  # noqa: E402
    send_telegram_startup_message,
)

