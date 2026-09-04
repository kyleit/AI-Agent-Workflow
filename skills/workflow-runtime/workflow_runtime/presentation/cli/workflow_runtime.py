# workflow_runtime.py
# QUICK-038: Block direct file execution -- guard must be first
import sys as _sys

if _sys.argv[0].endswith("workflow_runtime.py") and __name__ == "__main__":
    _sys.stderr.write(
        "ERROR: Do not run this module file directly.\n"
        "Use: python -m workflow_runtime <subcommand> [args]\n"
    )
    _sys.exit(127)

from workflow_runtime.presentation.cli.commands._impl.agent.analysis_agent import \
    do_analysis_agent
from workflow_runtime.presentation.cli.commands._impl.agent.test_runner import \
    do_test_action
from workflow_runtime.presentation.cli.commands._impl.config.config_manager import (
    do_config_action, do_permission, do_registry, do_rules_action)
from workflow_runtime.presentation.cli.commands._impl.context_manager import (
    do_context, do_state_action)
from workflow_runtime.presentation.cli.commands._impl.dependency_handler import (
    do_conflict, do_dependency, do_deps, do_merge)
from workflow_runtime.presentation.cli.commands._impl.docs_migration import (
    do_cleanup_action, do_migration_action)
from workflow_runtime.presentation.cli.commands._impl.knowledge.knowledge_search import (
    do_knowledge_action, do_search_action)
from workflow_runtime.presentation.cli.commands._impl.knowledge.memory_manager import (
    do_env_action, do_mail_action, do_memory_action)
from workflow_runtime.presentation.cli.commands._impl.project_manager import (
    do_implement_action, do_project_version_cached)
from workflow_runtime.presentation.cli.commands._impl.provider.provider_config import \
    do_provider_action
from workflow_runtime.presentation.cli.commands._impl.session.session_init import \
    do_init
from workflow_runtime.presentation.cli.commands._impl.session.session_lifecycle import (
    do_complete, do_continue_action, do_fail, do_heartbeat, do_lock,
    do_resume_action, do_start, do_status_action, do_step)
from workflow_runtime.presentation.cli.commands._impl.session.session_meta import (
    do_runtime_bus, do_session_command)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    RuntimeInputGate, ensure_project_registered_from_config,
    extract_work_item_id_from_text, get_current_project_context,
    is_telegram_daemon_running, sync_analysis_agents_to_session)
from workflow_runtime.presentation.cli.commands._impl.system.execution_control import \
    do_execution
from workflow_runtime.presentation.cli.commands._impl.system.runtime_bus import \
    do_runtime_action
from workflow_runtime.presentation.cli.commands._impl.system.system_health import (
    do_api_server, do_debug_action, do_doctor_action, do_notify_action,
    do_release_action, do_validate, do_verify_action)
from workflow_runtime.presentation.cli.commands._impl.ui.telegram_notify import \
    do_telegram
from workflow_runtime.presentation.cli.commands._impl.ui.ui_prompts import (
    do_choice, do_input, do_prompt)
from workflow_runtime.presentation.cli.commands._impl.ui.visual_debug import \
    do_visual_action
from workflow_runtime.presentation.cli.commands._impl.update.update_framework import \
    do_update
from workflow_runtime.presentation.cli.commands._impl.update.update_source_core import \
    do_update_source, _audit_workflow_document_quality, _capture_release_metadata_hashes, _capture_tree_hashes, _diff_tree_hashes, _has_release_metadata_changes, _has_workflow_documentation_changes, _has_workflow_report_changes, _prepare_agy_prompt_and_mode, _runtime_bus_response, _sanitize_artifact_tree, _sanitize_runtime_value, _read_json_file
from workflow_runtime.presentation.cli.commands._impl.usage.usage_report import \
    do_usage
from workflow_runtime.presentation.cli.commands._impl.workflow.orchestrator import \
    do_orchestrator
from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
    do_blueprint, do_compact, do_suggest, do_task, do_work_item_cached)
from workflow_runtime.presentation.cli.commands._impl.workflow.task_orchestrator import \
    do_task_orchestrator
from workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing import (
    do_active_workflow, do_classify_action, do_coordinator_action,
    do_discover_action, do_dispatch_action, do_routing, do_workflow)
# QUICK-039 P3: Backward-compat shim.
# All shared helpers moved to workflow_runtime_shared.py
# All do_* handlers moved to commands/_impl/
from workflow_runtime.presentation.cli.workflow_runtime_shared import (
    SessionLock, aggregate_state, calculate_project_fingerprint,
    check_context_drift, cleanup_lease, deconstruct_state,
    estimate_context_usage, get_checkpoint_name, get_git_info,
    get_global_summary, get_memory_info, get_permission_mode, get_project_id,
    get_project_summary, get_rag_info, get_version_info, get_workflow_summary,
    handle_sigterm, load_session, print_heartbeat, read_json_safe,
    requires_approval, save_session_atomic, save_usage_to_dbs,
    send_telegram_startup_message, sync_request_history, update_context_health,
    validate_checkpoint_level, write_json_atomic)

# QUICK-039 P3: All do_* handlers moved to commands/_impl/
# This file is now a backward-compat re-export shim.
# -------------------------------------------------------------------

__all__ = [
    "do_analysis_agent", "do_test_action", "do_config_action", "do_permission",
    "do_registry", "do_rules_action", "do_context", "do_state_action", "do_conflict",
    "do_dependency", "do_deps", "do_merge", "do_cleanup_action", "do_migration_action",
    "do_knowledge_action", "do_search_action", "do_env_action", "do_mail_action",
    "do_memory_action", "do_implement_action", "do_project_version_cached",
    "do_provider_action", "do_init", "do_complete", "do_fail", "do_heartbeat",
    "do_lock", "do_resume_action", "do_start", "do_status_action", "do_step",
    "do_continue_action",
    "do_runtime_bus", "do_session_command", "RuntimeInputGate",
    "ensure_project_registered_from_config",
    "extract_work_item_id_from_text", "get_current_project_context",
    "is_telegram_daemon_running", "sync_analysis_agents_to_session", "do_execution",
    "do_runtime_action", "do_api_server", "do_debug_action", "do_doctor_action",
    "do_notify_action", "do_release_action", "do_validate", "do_verify_action",
    "do_telegram", "do_choice", "do_input", "do_prompt", "do_visual_action",
    "do_update", "do_update_source",
    "do_usage", "do_orchestrator", "do_blueprint", "do_compact", "do_suggest",
    "do_task", "do_work_item_cached", "do_task_orchestrator", "do_active_workflow",
    "do_classify_action", "do_coordinator_action", "do_discover_action",
    "do_dispatch_action", "do_routing", "do_workflow", "SessionLock", "aggregate_state",
    "calculate_project_fingerprint", "check_context_drift", "cleanup_lease",
    "deconstruct_state", "estimate_context_usage", "get_checkpoint_name", "get_git_info",
    "get_global_summary", "get_memory_info", "get_permission_mode", "get_project_id",
    "get_project_summary", "get_rag_info", "get_version_info", "get_workflow_summary",
    "handle_sigterm", "load_session", "print_heartbeat", "read_json_safe",
    "requires_approval", "save_session_atomic", "save_usage_to_dbs",
    "send_telegram_startup_message", "sync_request_history", "update_context_health",
    "validate_checkpoint_level", "write_json_atomic"
]
