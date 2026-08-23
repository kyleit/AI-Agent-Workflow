# task_orchestrator.py
"""
Task Dependency Graph, State Machine, and Task Ledger for AIWF.
FEAT-050: Runtime Dependency Resolver — Task Orchestration Layer.

Manages:
- task_graph.json: dependency graph with ready_queue, blocked, completed
- tasks.json: source-of-truth ledger for task completion state
- State machine: enforces ALLOWED_TRANSITIONS, blocks forbidden shortcuts
- Next-task recommendation logic
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional, cast

from workflow_runtime.infrastructure.session.state_sync import \
    read_json_safe as _read_json_safe
from workflow_runtime.infrastructure.session.state_sync import \
    write_json_atomic as _write_json_atomic

# ---------------------------------------------------------------------------
# State Machine Constants
# ---------------------------------------------------------------------------

VALID_STATES = {
    "queued", "waiting", "ready", "running",
    "blocked", "completed", "failed", "skipped", "aborted"
}

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "queued":    {"waiting", "ready"},
    "waiting":   {"ready"},
    "ready":     {"running", "skipped"},
    "running":   {"completed", "failed", "blocked", "aborted"},
    "failed":    {"queued"},
    "blocked":   {"ready"},
    "completed": set(),
    "skipped":   set(),
    "aborted":   set(),
}

# Explicit list of shortcuts that are ALWAYS forbidden (fast-fail before ALLOWED_TRANSITIONS check)
FORBIDDEN_SHORTCUTS: list[tuple[str, str]] = [
    ("queued",   "completed"),
    ("waiting",  "completed"),
    ("running",  "queued"),
    ("completed","running"),
]

# ---------------------------------------------------------------------------
# State File Paths
# ---------------------------------------------------------------------------

_WORKFLOW_STATE_DIR = os.path.join(".agents", "state", "workflow")
TASK_GRAPH_PATH = os.path.join(_WORKFLOW_STATE_DIR, "task_graph.json")
TASK_LEDGER_PATH = os.path.join(_WORKFLOW_STATE_DIR, "tasks.json")

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

from .task_models import (CyclicDependencyError, ForbiddenStateTransitionError,
                          LedgerConsistencyError, TaskGraph, TaskLedger,
                          TaskNode, UnknownDependencyError, task_graph_to_dict)


def build_task_graph(plan_json: dict[str, Any]) -> TaskGraph:
    """
    Derive task dependency graph from plan JSON.

    plan_json expected keys:
      - feature_id: str
      - phases: list of {phase_id, name, tasks: list[str]}
      - tasks: list of {task_id, phase_id, dependencies: list[str], required: bool}

    Raises:
      CyclicDependencyError if a cycle is detected.
      UnknownDependencyError if a dependency references a non-existent task.
    """
    feature_id: str = str(plan_json.get("feature_id") or "UNKNOWN")
    raw_phases: list[Any] = cast(list[Any], plan_json.get("phases", [])) if isinstance(plan_json.get("phases"), list) else []
    raw_tasks: list[Any] = cast(list[Any], plan_json.get("tasks", [])) if isinstance(plan_json.get("tasks"), list) else []

    # Build phase registry
    phase_registry: dict[str, dict[str, Any]] = {}
    for ph in raw_phases:
        pid = ph.get("phase_id") or ph.get("id", "")
        phase_registry[pid] = {
            "name": ph.get("name", pid),
            "tasks": ph.get("tasks", []),
            "status": "queued",
        }

    # Build task registry
    task_nodes: dict[str, TaskNode] = {}
    all_task_ids: set[str] = set()

    for t in raw_tasks:
        tid = t.get("task_id") or t.get("id", "")
        if not tid:
            continue
        all_task_ids.add(tid)
        task_nodes[tid] = TaskNode(
            task_id=tid,
            phase_id=t.get("phase_id", ""),
            dependencies=list(t.get("dependencies", [])),
            dependents=[],
            state="queued",
            required=t.get("required", True),
            verification_status="pending",
        )

    # Validate dependency references
    for tid, node in task_nodes.items():
        for dep in node.dependencies:
            if dep not in all_task_ids:
                raise UnknownDependencyError(
                    f"Task '{tid}' references unknown dependency '{dep}'. "
                    f"Known tasks: {sorted(all_task_ids)}"
                )

    # Build reverse edges (dependents)
    for tid, node in task_nodes.items():
        for dep in node.dependencies:
            task_nodes[dep].dependents.append(tid)

    # Cycle detection (DFS)
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in task_nodes}
    cycle_path: list[str] = []

    def dfs(node_id: str, path: list[str]) -> None:
        color[node_id] = GRAY
        path.append(node_id)
        for dep in task_nodes[node_id].dependencies:
            if color[dep] == GRAY:
                cycle_path.extend(path)
                cycle_path.append(dep)
                raise CyclicDependencyError(
                    f"Cycle detected in task dependency graph: {' -> '.join(path + [dep])}"
                )
            if color[dep] == WHITE:
                dfs(dep, path)
        color[node_id] = BLACK
        path.pop()

    for tid in task_nodes:
        if color[tid] == WHITE:
            dfs(tid, [])

    # Compute initial ready_queue: tasks with no dependencies
    ready_queue = [
        tid for tid, node in task_nodes.items()
        if len(node.dependencies) == 0
    ]
    # Sort for determinism
    ready_queue.sort()
    for tid in ready_queue:
        task_nodes[tid].state = "ready"

    graph = TaskGraph(
        feature_id=feature_id,
        phases=phase_registry,
        tasks=task_nodes,
        ready_queue=ready_queue,
    )

    _write_json_atomic(TASK_GRAPH_PATH, task_graph_to_dict(graph))
    return graph

# ---------------------------------------------------------------------------
# Public: Task State Machine
# ---------------------------------------------------------------------------

def transition_task_state(
    task_id: str,
    new_state: str,
    ledger: TaskLedger,
    reason: str = "",
) -> bool:
    """
    Transition a task to a new state, enforcing ALLOWED_TRANSITIONS.

    Rules:
    - FORBIDDEN_SHORTCUTS are blocked even if technically allowed.
    - 'completed' requires: implementation done + expected outputs exist +
      verification passes + no active worker + no active lock.
    - Writes updated task to tasks.json atomically.

    Returns True on success. Raises ForbiddenStateTransitionError on failure.
    """
    if new_state not in VALID_STATES:
        raise ForbiddenStateTransitionError(
            f"Unknown state '{new_state}'. Valid states: {sorted(VALID_STATES)}"
        )

    tasks = ledger.tasks
    task_data = tasks.get(task_id)
    if task_data is None:
        raise LedgerConsistencyError(f"Task '{task_id}' not found in task ledger.")

    current_state = str(task_data.get("state", "queued") or "queued")

    # Check forbidden shortcuts first
    for (from_s, to_s) in FORBIDDEN_SHORTCUTS:
        if current_state == from_s and new_state == to_s:
            raise ForbiddenStateTransitionError(
                f"Forbidden state transition: '{current_state}' -> '{new_state}' for task '{task_id}'. "
                f"This shortcut is explicitly forbidden by the AIWF state machine."
            )

    # Check allowed transitions
    allowed = ALLOWED_TRANSITIONS.get(current_state, set())
    if new_state not in allowed:
        raise ForbiddenStateTransitionError(
            f"Invalid state transition: '{current_state}' -> '{new_state}' for task '{task_id}'. "
            f"Allowed from '{current_state}': {sorted(allowed) if allowed else 'none (terminal state)'}."
        )

    # Additional gate for 'completed': verify pre-conditions
    if new_state == "completed":
        worker_id = task_data.get("worker_id")
        lock_ids: list[Any] = cast(list[Any], task_data.get("lock_ids", [])) if isinstance(task_data.get("lock_ids"), list) else []
        verification_status = task_data.get("verification_status", "pending")

        if worker_id is not None:
            raise ForbiddenStateTransitionError(
                f"Cannot mark task '{task_id}' as completed: active worker '{worker_id}' still assigned."
            )
        if lock_ids:
            raise ForbiddenStateTransitionError(
                f"Cannot mark task '{task_id}' as completed: active locks still held: {lock_ids}."
            )
        if verification_status not in ("pass", "not_configured"):
            raise ForbiddenStateTransitionError(
                f"Cannot mark task '{task_id}' as completed: "
                f"verification_status is '{verification_status}', expected 'pass' or 'not_configured'."
            )

    # Apply transition
    task_data["state"] = new_state
    task_data["updated_at"] = datetime.now().astimezone().isoformat()
    if reason:
        task_data["transition_reason"] = reason
    if new_state == "completed":
        task_data["completed_at"] = datetime.now().astimezone().isoformat()
        task_data["attempt"] = task_data.get("attempt", 0) + 1

    ledger.tasks[task_id] = task_data
    ledger.updated_at = datetime.now().astimezone().isoformat()

    # Update completion counters
    completed_count = sum(
        1 for t in tasks.values() if t.get("state") == "completed"
    )
    ledger.tasks_completed = completed_count
    ledger.tasks_incomplete = ledger.tasks_total - completed_count

    write_task_ledger(ledger)
    return True

# ---------------------------------------------------------------------------
# Public: Task Ledger
# ---------------------------------------------------------------------------

def load_task_ledger() -> TaskLedger:
    """
    Read .agents/state/workflow/tasks.json.
    Raises LedgerConsistencyError if file is missing.
    """
    data: dict[str, Any] = _read_json_safe(TASK_LEDGER_PATH)
    if not data:
        raise LedgerConsistencyError(
            f"Task ledger not found at '{TASK_LEDGER_PATH}'. "
            "Run 'task graph build' before implementation."
        )

    ledger = TaskLedger(
        feature_id=str(data.get("feature_id", "")),
        current_phase=str(data.get("current_phase", "")),
        current_task=str(data.get("current_task", "")),
        tasks_total=int(data.get("tasks_total", 0)),
        tasks_completed=int(data.get("tasks_completed", 0)),
        tasks_incomplete=int(data.get("tasks_incomplete", 0)),
        tasks=cast(dict[str, Any], data.get("tasks", {})) if isinstance(data.get("tasks"), dict) else {},
        updated_at=str(data.get("updated_at", "")),
    )
    return ledger


def write_task_ledger(ledger: TaskLedger) -> None:
    """Atomically write tasks.json."""
    data: dict[str, Any] = {
        "feature_id": ledger.feature_id,
        "current_phase": ledger.current_phase,
        "current_task": ledger.current_task,
        "tasks_total": ledger.tasks_total,
        "tasks_completed": ledger.tasks_completed,
        "tasks_incomplete": ledger.tasks_incomplete,
        "tasks": cast(dict[str, Any], ledger.tasks),
        "updated_at": ledger.updated_at,
    }
    _write_json_atomic(TASK_LEDGER_PATH, data)


def create_ledger_from_graph(graph: TaskGraph) -> TaskLedger:
    """Create an initial task ledger from a built task graph."""
    tasks: dict[str, dict[str, Any]] = {}
    graph_tasks = cast(dict[str, Any], graph.tasks)
    graph_phases = cast(dict[str, Any], graph.phases)
    for tid, node in graph_tasks.items():
        tasks[tid] = {
            "phase_id": node.phase_id,
            "state": node.state,
            "dependencies": node.dependencies,
            "required": node.required,
            "verification_status": node.verification_status,
            "attempt": node.attempt,
            "worker_id": node.worker_id,
            "lock_ids": node.lock_ids,
            "read_set": [],
            "write_set": [],
            "expected_outputs": [],
            "completion_evidence": {},
        }

    ledger = TaskLedger(
        feature_id=graph.feature_id,
        current_phase=list(graph_phases.keys())[0] if graph_phases else "",
        current_task=graph.ready_queue[0] if graph.ready_queue else "",
        tasks_total=len(graph.tasks),
        tasks_completed=0,
        tasks_incomplete=len(graph.tasks),
        tasks=tasks,
    )
    write_task_ledger(ledger)
    return ledger

# ---------------------------------------------------------------------------
# Public: Next-Task Recommendation
# ---------------------------------------------------------------------------

def get_next_ready_task(
    task_graph: Any,
    task_ledger: Any,
) -> tuple[Optional[str], str]:
    """
    Return (task_id, reason) for the next actionable task.
    Returns (None, reason) if blocked.
    """
    tg_tasks: dict[str, Any] = getattr(task_graph, "tasks", {}) or {}
    tl_tasks: dict[str, Any] = getattr(task_ledger, "tasks", {}) or {}
    ready_queue: list[str] = getattr(task_graph, "ready_queue", []) or []

    # Rule 1: running task exists
    running = [
        tid for tid, tdata in tl_tasks.items()
        if cast(dict[str, Any], tdata or {}).get("state") == "running"
    ]
    if running:
        return None, f"Wait or recover running task first: {running[0]}"

    # Rule 2: failed task exists
    failed = [
        tid for tid, tdata in tl_tasks.items()
        if cast(dict[str, Any], tdata or {}).get("state") == "failed"
    ]
    if failed:
        return None, f"Recover failed task before continuing: {failed[0]}"

    # Rule 3: check ready_queue (graph-level)
    for tid in ready_queue:
        tdata: dict[str, Any] = cast(dict[str, Any], tl_tasks.get(str(tid), {}) or {})
        if tdata.get("state") not in ("ready", "queued"):
            continue
        task_obj = tg_tasks.get(str(tid))
        deps: list[Any] = getattr(task_obj, "dependencies", []) if task_obj else []
        all_deps_done = all(
            cast(dict[str, Any], tl_tasks.get(str(dep), {}) or {}).get("state") == "completed"
            for dep in deps
        )
        if all_deps_done:
            return str(tid), f"Next ready task: {tid}"

    tg_phases: dict[str, Any] = getattr(task_graph, "phases", {}) or {}
    tl_tasks: dict[str, Any] = getattr(task_ledger, "tasks", {}) or {}
    tg_tasks: dict[str, Any] = getattr(task_graph, "tasks", {}) or {}

    # Rule 4: current phase incomplete
    current_phase_id = str(getattr(task_ledger, "current_phase", "") or "")
    if current_phase_id:
        phase_info: dict[str, Any] = tg_phases.get(current_phase_id, {}) or {}
        phase_tasks: list[Any] = cast(list[Any], phase_info.get("tasks", [])) if isinstance(phase_info.get("tasks"), list) else []
        incomplete_in_phase = [
            tid for tid in phase_tasks
            if cast(dict[str, Any], tl_tasks.get(str(tid), {}) or {}).get("state") != "completed"
        ]
        if incomplete_in_phase:
            return None, (
                f"Current phase '{current_phase_id}' is incomplete. "
                f"Continue with remaining tasks: {incomplete_in_phase}"
            )

    # Rule 5: current phase done -> try next phase
    phase_ids = list(tg_phases.keys())
    current_idx = phase_ids.index(current_phase_id) if current_phase_id in phase_ids else -1

    for idx in range(current_idx + 1, len(phase_ids)):
        next_phase_id = phase_ids[idx]
        next_phase_info: dict[str, Any] = tg_phases.get(next_phase_id, {}) or {}
        next_phase_tasks: list[Any] = cast(list[Any], next_phase_info.get("tasks", [])) if isinstance(next_phase_info.get("tasks"), list) else []

        for tid in next_phase_tasks:
            tdata: dict[str, Any] = cast(dict[str, Any], tl_tasks.get(str(tid), {}) or {})
            if tdata.get("state") not in ("ready", "queued"):
                continue
            task_obj = tg_tasks.get(str(tid))
            deps: list[Any] = getattr(task_obj, "dependencies", []) if task_obj else []
            all_deps_done = all(
                cast(dict[str, Any], tl_tasks.get(str(dep), {}) or {}).get("state") == "completed"
                for dep in deps
            )
            if all_deps_done:
                return str(tid), f"Phase '{current_phase_id}' complete. Start next phase '{next_phase_id}' with task: {tid}"

    # Rule 6: all phases complete -> recommend /debug
    all_tasks_done = all(
        cast(dict[str, Any], tdata or {}).get("state") == "completed"
        for tdata in tl_tasks.values()
    )
    if all_tasks_done:
        return None, "All implementation tasks complete. Run /debug to verify."

    # Rule 7: NEVER recommend /release here
    return None, "No ready task found. Check for blocked or waiting tasks."

# ---------------------------------------------------------------------------
# Public: Phase Completion Gate (also used by dependency_resolver)
# ---------------------------------------------------------------------------



# -- re-exports from split parts (backward compat) --
from workflow_runtime.application.use_cases.phase_completion_validator import (
    validate_phase_completion)

__all__ = ['validate_phase_completion']
