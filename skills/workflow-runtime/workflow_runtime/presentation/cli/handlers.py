"""Backward-compatible re-exports from semantic command handlers."""
from __future__ import annotations

from .knowledge_command_handlers import (
    handle_cleanup, handle_execution, handle_memory, handle_notify,
    handle_provider, handle_registry, handle_search, handle_state,
    handle_telegram, handle_visual)
from .runtime_command_handlers import (
    handle_config, handle_deps, handle_doctor, handle_init, handle_migration,
    handle_permissions, handle_release, handle_runbook, handle_runtime)
from .session_command_handlers import (
    handle_heartbeat, handle_mail, handle_prompt, handle_session)
from .workflow_command_handlers import (
    handle_blueprint, handle_complete, handle_coordinator, handle_dispatch,
    handle_fail, handle_start, handle_step, handle_suggest, handle_validate,
    handle_verify, handle_workflow)

__all__ = [
    "handle_dispatch",
    "handle_coordinator",
    "handle_notify",
    "handle_cleanup",
    "handle_verify",
    "handle_search",
    "handle_memory",
    "handle_state",
    "handle_telegram",
    "handle_registry",
    "handle_session",
    "handle_execution",
    "handle_doctor",
    "handle_runtime",
    "handle_workflow",
    "handle_provider",
    "handle_release",
    "handle_visual",
    "handle_init",
    "handle_config",
    "handle_runbook",
    "handle_deps",
    "handle_permissions",
    "handle_migration",
    "handle_validate",
    "handle_start",
    "handle_step",
    "handle_complete",
    "handle_fail",
    "handle_heartbeat",
    "handle_blueprint",
    "handle_suggest",
    "handle_prompt",
    "handle_mail",
]
