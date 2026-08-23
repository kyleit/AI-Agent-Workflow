from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Any

import workflow_runtime.application.use_cases.task_orchestrator as task_use_cases
from workflow_runtime.application.use_cases.task_orchestrator import (
    TASK_GRAPH_PATH, TASK_LEDGER_PATH, build_task_graph,
    create_ledger_from_graph, get_next_ready_task, load_task_ledger,
    transition_task_state)
from workflow_runtime.infrastructure.session.state_sync import read_json_safe
from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
    do_task)


def do_task_orchestrator(args: argparse.Namespace) -> None:
    """Task dependency graph, state machine, and next-task recommendation CLI handler."""
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)

    if subaction == "graph":
        graph_action = getattr(args, "graph_action", None)
        if graph_action == "build":
            feature_id = str(getattr(args, "feature", "") or "")
            plan_paths = [
                os.path.join("docs", "plans", f"{feature_id}_*.json"),
                os.path.join("docs", "plans", f"{feature_id}.json"),
            ]
            plan_json: dict[str, Any] | None = None
            for pattern in plan_paths:
                matches = glob.glob(pattern)
                if matches:
                    plan_json = read_json_safe(matches[0])
                    break
            if not plan_json:
                bp_paths = list(glob.glob(os.path.join("docs", "designs", f"{feature_id}_*.json")))
                if bp_paths:
                    plan_json = read_json_safe(bp_paths[0])

            if not plan_json:
                print(f"No plan JSON found for feature '{feature_id}'. Expected at docs/plans/{feature_id}_*.json", file=sys.stderr)
                sys.exit(1)

            try:
                graph = build_task_graph(plan_json)
                ledger = create_ledger_from_graph(graph)
                print(f"Task graph built: {len(graph.tasks)} tasks, {len(graph.ready_queue)} ready.")
                print(f"Written to: {TASK_GRAPH_PATH}")
                print(f"Ledger written to: {TASK_LEDGER_PATH}")
            except Exception as e:
                print(f"[task graph build] Error: {e}", file=sys.stderr)
                sys.exit(1)

        elif graph_action == "status":
            graph_data = read_json_safe(TASK_GRAPH_PATH)
            if not graph_data or not graph_data.get("tasks"):
                print("No task graph found. Run 'task graph build --feature FEAT-XXX' first.")
                sys.exit(0)
            print(f"\nTask Graph: {graph_data.get('feature_id', 'unknown')}")
            print(f"Ready: {graph_data.get('ready_queue', [])}")
            print(f"Blocked: {graph_data.get('blocked_tasks', [])}")
            print(f"Completed: {graph_data.get('completed_tasks', [])}")
            print(f"Failed: {graph_data.get('failed_tasks', [])}")

    elif subaction == "state":
        state_action = getattr(args, "state_action", None)
        if state_action == "transition":
            try:
                ledger = load_task_ledger()
                graph_fn: Any = getattr(task_use_cases, "_task_graph_from_dict", None)
                graph_data = read_json_safe(TASK_GRAPH_PATH)
                graph = graph_fn(graph_data) if callable(graph_fn) and graph_data else None
                task_id = str(getattr(args, "task_id", "") or "")
                new_state = str(getattr(args, "new_state", "") or "")
                reason = str(getattr(args, "reason", "") or "")
                result = transition_task_state(task_id, new_state, ledger, reason)
                if result:
                    print(f"Transitioned '{task_id}' to '{new_state}'.")
            except Exception as e:
                print(f"[task state transition] Error: {e}", file=sys.stderr)
                sys.exit(1)

    elif subaction == "next":
        try:
            graph_fn: Any = getattr(task_use_cases, "_task_graph_from_dict", None)
            graph_data = read_json_safe(TASK_GRAPH_PATH)
            ledger = load_task_ledger()
            graph = graph_fn(graph_data) if callable(graph_fn) and graph_data else None
            if graph is None:
                print("No task graph. Run 'task graph build' first.")
                sys.exit(1)
            next_task, reason = get_next_ready_task(graph, ledger)
            if next_task:
                print(f"Next task: {next_task}")
                print(f"Reason: {reason}")
            else:
                print(f"No ready task: {reason}")
                sys.exit(1)
        except Exception as e:
            print(f"[task next] Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif subaction in ("plan", "start", "complete", "fail"):
        do_task(args)


__all__ = ["do_task_orchestrator"]
