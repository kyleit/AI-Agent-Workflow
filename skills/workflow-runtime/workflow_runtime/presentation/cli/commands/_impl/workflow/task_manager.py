"""
workflow_runtime/presentation/cli/commands/_impl/workflow/task_manager.py

Facade re-exporting task command dispatcher and state synchronizer functions.
"""
from __future__ import annotations

from workflow_runtime.presentation.cli.commands._impl.workflow.task_command_dispatcher import (
    do_blueprint, do_compact, do_suggest, do_task, do_work_item_cached)
from workflow_runtime.presentation.cli.commands._impl.workflow.task_state_synchronizer import (
    sync_execution_state_to_session)

__all__ = [
    "do_task",
    "do_blueprint",
    "do_suggest",
    "do_compact",
    "do_work_item_cached",
    "sync_execution_state_to_session",
]
