from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional, cast

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

FORBIDDEN_SHORTCUTS: list[tuple[str, str]] = [
    ("queued",   "completed"),
    ("waiting",  "completed"),
    ("running",  "queued"),
    ("completed","running"),
]

_WORKFLOW_STATE_DIR = os.path.join(".agents", "state", "workflow")
TASK_GRAPH_PATH = os.path.join(_WORKFLOW_STATE_DIR, "task_graph.json")
TASK_LEDGER_PATH = os.path.join(_WORKFLOW_STATE_DIR, "tasks.json")


class CyclicDependencyError(Exception):
    """Raised when a cycle is detected in the task dependency graph."""


class UnknownDependencyError(Exception):
    """Raised when a task references a non-existent dependency."""


class ForbiddenStateTransitionError(Exception):
    """Raised when a forbidden state transition is attempted."""


class LedgerConsistencyError(Exception):
    """Raised when a blueprint task is missing from tasks.json ledger."""


@dataclass
class TaskNode:
    task_id: str
    phase_id: str
    dependencies: list[str] = field(default_factory=list[str])
    dependents: list[str] = field(default_factory=list[str])
    state: str = "queued"
    required: bool = True
    verification_status: str = "pending"   # pending | pass | fail | not_configured
    attempt: int = 0
    worker_id: Optional[str] = None
    lock_ids: list[str] = field(default_factory=list[str])
    approved_skip_reason: Optional[str] = None


@dataclass
class TaskGraph:
    feature_id: str
    graph_version: str = "1.0.0"
    phases: dict[str, dict[str, Any]] = field(default_factory=dict[str, dict[str, Any]])
    tasks: dict[str, TaskNode] = field(default_factory=dict[str, TaskNode])
    ready_queue: list[str] = field(default_factory=list[str])
    blocked_tasks: list[str] = field(default_factory=list[str])
    failed_tasks: list[str] = field(default_factory=list[str])
    completed_tasks: list[str] = field(default_factory=list[str])
    created_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())


@dataclass
class TaskLedger:
    feature_id: str
    current_phase: str = ""
    current_task: str = ""
    tasks_total: int = 0
    tasks_completed: int = 0
    tasks_incomplete: int = 0
    tasks: dict[str, dict[str, Any]] = field(default_factory=dict[str, dict[str, Any]])
    updated_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())


@dataclass
class PhaseCoverageResult:
    ok: bool
    phase_id: str
    incomplete_tasks: list[str] = field(default_factory=list[str])
    failed_criteria: list[str] = field(default_factory=list[str])


def _write_json_atomic(file_path: str, data: Any) -> None:
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _read_json_safe(file_path: str) -> dict[str, Any]:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def _task_node_to_dict(node: TaskNode) -> dict[str, Any]:
    d: dict[str, Any] = asdict(node)
    return d


def _task_graph_to_dict(graph: TaskGraph) -> dict[str, Any]:
    d: dict[str, Any] = {
        "feature_id": graph.feature_id,
        "graph_version": graph.graph_version,
        "phases": graph.phases,
        "tasks": {tid: _task_node_to_dict(n) for tid, n in graph.tasks.items()},
        "ready_queue": graph.ready_queue,
        "blocked_tasks": graph.blocked_tasks,
        "failed_tasks": graph.failed_tasks,
        "completed_tasks": graph.completed_tasks,
        "created_at": graph.created_at,
        "updated_at": graph.updated_at,
    }
    return d


def _task_node_from_dict(d: dict[str, Any]) -> TaskNode:
    raw_deps = d.get("dependencies", [])
    deps: list[str] = [str(x) for x in cast(list[Any], raw_deps)] if isinstance(raw_deps, list) else []
    raw_dependents = d.get("dependents", [])
    dependents: list[str] = [str(x) for x in cast(list[Any], raw_dependents)] if isinstance(raw_dependents, list) else []
    raw_locks = d.get("lock_ids", [])
    locks: list[str] = [str(x) for x in cast(list[Any], raw_locks)] if isinstance(raw_locks, list) else []

    worker_id_val = d.get("worker_id")
    skip_reason_val = d.get("approved_skip_reason")

    return TaskNode(
        task_id=str(d.get("task_id", "")),
        phase_id=str(d.get("phase_id", "")),
        dependencies=deps,
        dependents=dependents,
        state=str(d.get("state", "queued")),
        required=bool(d.get("required", True)),
        verification_status=str(d.get("verification_status", "pending")),
        attempt=int(d.get("attempt", 0)),
        worker_id=str(worker_id_val) if worker_id_val is not None else None,
        lock_ids=locks,
        approved_skip_reason=str(skip_reason_val) if skip_reason_val is not None else None,
    )


def _task_graph_from_dict(d: dict[str, Any]) -> TaskGraph:
    raw_tasks = d.get("tasks", {})
    tasks_dict: dict[str, Any] = cast(dict[str, Any], raw_tasks) if isinstance(raw_tasks, dict) else {}
    parsed_tasks: dict[str, TaskNode] = {}
    for tid, tn_raw in tasks_dict.items():
        if isinstance(tn_raw, dict):
            parsed_tasks[str(tid)] = _task_node_from_dict(cast(dict[str, Any], tn_raw))

    raw_phases = d.get("phases", {})
    phases_dict: dict[str, dict[str, Any]] = cast(dict[str, dict[str, Any]], raw_phases) if isinstance(raw_phases, dict) else {}

    raw_rq = d.get("ready_queue", [])
    ready_queue: list[str] = [str(x) for x in cast(list[Any], raw_rq)] if isinstance(raw_rq, list) else []
    raw_bt = d.get("blocked_tasks", [])
    blocked_tasks: list[str] = [str(x) for x in cast(list[Any], raw_bt)] if isinstance(raw_bt, list) else []
    raw_ft = d.get("failed_tasks", [])
    failed_tasks: list[str] = [str(x) for x in cast(list[Any], raw_ft)] if isinstance(raw_ft, list) else []
    raw_ct = d.get("completed_tasks", [])
    completed_tasks: list[str] = [str(x) for x in cast(list[Any], raw_ct)] if isinstance(raw_ct, list) else []

    return TaskGraph(
        feature_id=str(d.get("feature_id", "")),
        graph_version=str(d.get("graph_version", "1.0.0")),
        phases=phases_dict,
        tasks=parsed_tasks,
        ready_queue=ready_queue,
        blocked_tasks=blocked_tasks,
        failed_tasks=failed_tasks,
        completed_tasks=completed_tasks,
        created_at=str(d.get("created_at", datetime.now().astimezone().isoformat())),
        updated_at=str(d.get("updated_at", datetime.now().astimezone().isoformat())),
    )


write_json_atomic = _write_json_atomic
read_json_safe = _read_json_safe
task_graph_to_dict = _task_graph_to_dict
task_node_to_dict = _task_node_to_dict
task_node_from_dict = _task_node_from_dict
task_graph_from_dict = _task_graph_from_dict


__all__ = [
    "VALID_STATES",
    "ALLOWED_TRANSITIONS",
    "FORBIDDEN_SHORTCUTS",
    "TASK_GRAPH_PATH",
    "TASK_LEDGER_PATH",
    "CyclicDependencyError",
    "UnknownDependencyError",
    "ForbiddenStateTransitionError",
    "LedgerConsistencyError",
    "TaskNode",
    "TaskGraph",
    "TaskLedger",
    "PhaseCoverageResult",
    "write_json_atomic",
    "read_json_safe",
    "task_graph_to_dict",
    "task_node_to_dict",
    "task_node_from_dict",
    "task_graph_from_dict",
]
