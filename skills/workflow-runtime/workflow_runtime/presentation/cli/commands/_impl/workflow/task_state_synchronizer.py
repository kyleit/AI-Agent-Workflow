"""
workflow_runtime/presentation/cli/commands/_impl/workflow/task_state_synchronizer.py

Session state synchronizer for parallel tasks and execution mode.
"""
from __future__ import annotations

import json
import os
from typing import Any, cast

from workflow_runtime.infrastructure.session.session_io import (
    load_session, save_session_atomic)


def sync_execution_state_to_session() -> None:
    session = load_session()
    if not session:
        return

    plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
    if os.path.exists(plan_file):
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = cast(dict[str, Any], json.load(f))
                session["implementation_execution_mode"] = plan_data.get("implementation_execution_mode", "pending")
                session["parallel_allowed_phase"] = plan_data.get("parallel_allowed_phase", "implementation")
                session["parallel_allowed"] = plan_data.get("parallel_allowed", False)
                session["execution_mode"] = plan_data.get("implementation_execution_mode", "pending")
                session["recommended_mode"] = plan_data.get("recommended_mode", "parallel")
                session["approved"] = plan_data.get("approved", False)
        except Exception:
            pass

    tasks_file = os.path.join(".agents", "runtime", "parallel-tasks.json")
    parallel_groups: list[str] = []
    running_agents: list[str] = []
    queued_agents: list[str] = []
    blocked_agents: list[str] = []
    waiting_dependencies: list[str] = []

    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks_data = cast(dict[str, Any], json.load(f))
                raw_tasks = tasks_data.get("tasks")
                tasks: dict[str, Any] = cast(dict[str, Any], raw_tasks) if isinstance(raw_tasks, dict) else {}
                for tid, tinfo in tasks.items():
                    if isinstance(tinfo, dict):
                        t_dict = cast(dict[str, Any], tinfo)
                        status = str(t_dict.get("status", "pending"))
                        group = str(t_dict.get("execution_group", ""))
                        if group and group not in parallel_groups:
                            parallel_groups.append(group)
                        if status == "running":
                            running_agents.append(str(tid))
                        elif status == "pending":
                            queued_agents.append(str(tid))
                        elif status == "blocked":
                            blocked_agents.append(str(tid))
        except Exception:
            pass

    session["parallel_groups"] = parallel_groups
    session["running_agents"] = running_agents
    session["queued_agents"] = queued_agents
    session["blocked_agents"] = blocked_agents
    session["waiting_dependencies"] = waiting_dependencies

    save_session_atomic(session)


__all__ = ["sync_execution_state_to_session"]
