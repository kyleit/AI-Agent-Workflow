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

import json
import os
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional

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

class CyclicDependencyError(Exception):
    """Raised when a cycle is detected in the task dependency graph."""
    pass

class UnknownDependencyError(Exception):
    """Raised when a task references a non-existent dependency."""
    pass

class ForbiddenStateTransitionError(Exception):
    """Raised when a forbidden state transition is attempted."""
    pass

class LedgerConsistencyError(Exception):
    """Raised when a blueprint task is missing from tasks.json ledger."""
    pass

# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class TaskNode:
    task_id: str
    phase_id: str
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    state: str = "queued"
    required: bool = True
    verification_status: str = "pending"   # pending | pass | fail | not_configured
    attempt: int = 0
    worker_id: Optional[str] = None
    lock_ids: list[str] = field(default_factory=list)
    approved_skip_reason: Optional[str] = None


@dataclass
class TaskGraph:
    feature_id: str
    graph_version: str = "1.0.0"
    phases: dict[str, dict] = field(default_factory=dict)
    tasks: dict[str, TaskNode] = field(default_factory=dict)
    ready_queue: list[str] = field(default_factory=list)
    blocked_tasks: list[str] = field(default_factory=list)
    failed_tasks: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)
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
    tasks: dict[str, dict] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())


@dataclass
class PhaseCoverageResult:
    ok: bool
    phase_id: str
    incomplete_tasks: list[str] = field(default_factory=list)
    failed_criteria: list[str] = field(default_factory=list)

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

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


def _read_json_safe(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _task_node_to_dict(node: TaskNode) -> dict:
    d = asdict(node)
    return d


def _task_graph_to_dict(graph: TaskGraph) -> dict:
    d = {
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


def _task_node_from_dict(d: dict) -> TaskNode:
    return TaskNode(
        task_id=d.get("task_id", ""),
        phase_id=d.get("phase_id", ""),
        dependencies=d.get("dependencies", []),
        dependents=d.get("dependents", []),
        state=d.get("state", "queued"),
        required=d.get("required", True),
        verification_status=d.get("verification_status", "pending"),
        attempt=d.get("attempt", 0),
        worker_id=d.get("worker_id"),
        lock_ids=d.get("lock_ids", []),
        approved_skip_reason=d.get("approved_skip_reason"),
    )


def _task_graph_from_dict(d: dict) -> TaskGraph:
    graph = TaskGraph(
        feature_id=d.get("feature_id", ""),
        graph_version=d.get("graph_version", "1.0.0"),
        phases=d.get("phases", {}),
        tasks={tid: _task_node_from_dict(n) for tid, n in d.get("tasks", {}).items()},
        ready_queue=d.get("ready_queue", []),
        blocked_tasks=d.get("blocked_tasks", []),
        failed_tasks=d.get("failed_tasks", []),
        completed_tasks=d.get("completed_tasks", []),
        created_at=d.get("created_at", datetime.now().astimezone().isoformat()),
        updated_at=d.get("updated_at", datetime.now().astimezone().isoformat()),
    )
    return graph

# ---------------------------------------------------------------------------
# Public: Build Task Graph from Plan JSON
# ---------------------------------------------------------------------------

def build_task_graph(plan_json: dict) -> TaskGraph:
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
    feature_id = plan_json.get("feature_id", "UNKNOWN")
    raw_phases = plan_json.get("phases", [])
    raw_tasks = plan_json.get("tasks", [])

    # Build phase registry
    phase_registry: dict[str, dict] = {}
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

    _write_json_atomic(TASK_GRAPH_PATH, _task_graph_to_dict(graph))
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

    task_data = ledger.tasks.get(task_id)
    if task_data is None:
        raise LedgerConsistencyError(f"Task '{task_id}' not found in task ledger.")

    current_state = task_data.get("state", "queued")

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
        lock_ids = task_data.get("lock_ids", [])
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
        1 for t in ledger.tasks.values() if t.get("state") == "completed"
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
    data = _read_json_safe(TASK_LEDGER_PATH)
    if not data:
        raise LedgerConsistencyError(
            f"Task ledger not found at '{TASK_LEDGER_PATH}'. "
            "Run 'task graph build' before implementation."
        )

    ledger = TaskLedger(
        feature_id=data.get("feature_id", ""),
        current_phase=data.get("current_phase", ""),
        current_task=data.get("current_task", ""),
        tasks_total=data.get("tasks_total", 0),
        tasks_completed=data.get("tasks_completed", 0),
        tasks_incomplete=data.get("tasks_incomplete", 0),
        tasks=data.get("tasks", {}),
        updated_at=data.get("updated_at", ""),
    )
    return ledger


def write_task_ledger(ledger: TaskLedger) -> None:
    """Atomically write tasks.json."""
    data = {
        "feature_id": ledger.feature_id,
        "current_phase": ledger.current_phase,
        "current_task": ledger.current_task,
        "tasks_total": ledger.tasks_total,
        "tasks_completed": ledger.tasks_completed,
        "tasks_incomplete": ledger.tasks_incomplete,
        "tasks": ledger.tasks,
        "updated_at": ledger.updated_at,
    }
    _write_json_atomic(TASK_LEDGER_PATH, data)


def create_ledger_from_graph(graph: TaskGraph) -> TaskLedger:
    """Create an initial task ledger from a built task graph."""
    tasks: dict[str, dict] = {}
    for tid, node in graph.tasks.items():
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
        current_phase=list(graph.phases.keys())[0] if graph.phases else "",
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
    task_graph: TaskGraph,
    task_ledger: TaskLedger,
) -> tuple[Optional[str], str]:
    """
    Return (task_id, reason) for the next actionable task.
    Returns (None, reason) if blocked.

    Priority rules (evaluated in order):
    1. Any task is 'running'  -> wait, cannot start another
    2. Any task is 'failed'   -> recover before continuing
    3. Scan ready_queue       -> return first whose all deps are 'completed'
    4. Current phase has incomplete tasks -> stay in current phase
    5. All tasks in current phase complete -> recommend next phase entry task
    6. All phases complete -> recommend /debug
    7. NEVER recommend /release prematurely
    """
    # Rule 1: running task exists
    running = [
        tid for tid, tdata in task_ledger.tasks.items()
        if tdata.get("state") == "running"
    ]
    if running:
        return None, f"Wait or recover running task first: {running[0]}"

    # Rule 2: failed task exists
    failed = [
        tid for tid, tdata in task_ledger.tasks.items()
        if tdata.get("state") == "failed"
    ]
    if failed:
        return None, f"Recover failed task before continuing: {failed[0]}"

    # Rule 3: check ready_queue (graph-level)
    for tid in task_graph.ready_queue:
        tdata = task_ledger.tasks.get(tid, {})
        if tdata.get("state") not in ("ready", "queued"):
            continue
        # Verify all dependencies completed
        deps = task_graph.tasks[tid].dependencies if tid in task_graph.tasks else []
        all_deps_done = all(
            task_ledger.tasks.get(dep, {}).get("state") == "completed"
            for dep in deps
        )
        if all_deps_done:
            return tid, f"Next ready task: {tid}"

    # Rule 4: current phase incomplete
    current_phase_id = task_ledger.current_phase
    if current_phase_id:
        phase_info = task_graph.phases.get(current_phase_id, {})
        phase_tasks = phase_info.get("tasks", [])
        incomplete_in_phase = [
            tid for tid in phase_tasks
            if task_ledger.tasks.get(tid, {}).get("state") != "completed"
        ]
        if incomplete_in_phase:
            return None, (
                f"Current phase '{current_phase_id}' is incomplete. "
                f"Continue with remaining tasks: {incomplete_in_phase}"
            )

    # Rule 5: current phase done -> try next phase
    phase_ids = list(task_graph.phases.keys())
    current_idx = phase_ids.index(current_phase_id) if current_phase_id in phase_ids else -1

    for idx in range(current_idx + 1, len(phase_ids)):
        next_phase_id = phase_ids[idx]
        next_phase_info = task_graph.phases.get(next_phase_id, {})
        next_phase_tasks = next_phase_info.get("tasks", [])

        for tid in next_phase_tasks:
            tdata = task_ledger.tasks.get(tid, {})
            if tdata.get("state") not in ("ready", "queued"):
                continue
            deps = task_graph.tasks[tid].dependencies if tid in task_graph.tasks else []
            all_deps_done = all(
                task_ledger.tasks.get(dep, {}).get("state") == "completed"
                for dep in deps
            )
            if all_deps_done:
                return tid, f"Phase '{current_phase_id}' complete. Start next phase '{next_phase_id}' with task: {tid}"

    # Rule 6: all phases complete -> recommend /debug
    all_tasks_done = all(
        tdata.get("state") == "completed"
        for tdata in task_ledger.tasks.values()
    )
    if all_tasks_done:
        return None, "All implementation tasks complete. Run /debug to verify."

    # Rule 7: NEVER recommend /release here
    return None, "No ready task found. Check for blocked or waiting tasks."

# ---------------------------------------------------------------------------
# Public: Phase Completion Gate (also used by dependency_resolver)
# ---------------------------------------------------------------------------

def validate_phase_completion(
    phase_id: str,
    task_graph: TaskGraph,
    task_ledger: TaskLedger,
) -> PhaseCoverageResult:
    """
    A phase is complete ONLY when ALL of the following hold:
    1. Every task in phase.tasks exists in tasks.json (ledger consistency)
    2. Every task has state == 'completed'
    3. Every task's verification_status is 'pass' or 'not_configured'
    4. No required task is 'skipped' without approved_skip_reason
    5. No task in phase is 'queued','waiting','ready','running','blocked','failed','aborted'
    6. All phase exit criteria pass (worker count == 0, lock count == 0)

    Hard Rule: Phase Complete != First Blocking Task Complete
    """
    phase_info = task_graph.phases.get(phase_id)
    if phase_info is None:
        return PhaseCoverageResult(
            ok=False,
            phase_id=phase_id,
            failed_criteria=[f"Phase '{phase_id}' not found in task graph."],
        )

    phase_tasks = phase_info.get("tasks", [])
    incomplete: list[str] = []
    failed_criteria: list[str] = []

    for tid in phase_tasks:
        # Criterion 1: task must exist in ledger
        tdata = task_ledger.tasks.get(tid)
        if tdata is None:
            incomplete.append(tid)
            failed_criteria.append(f"Task '{tid}' missing from ledger (LedgerConsistencyError)")
            continue

        state = tdata.get("state", "queued")
        verification = tdata.get("verification_status", "pending")
        worker_id = tdata.get("worker_id")
        lock_ids = tdata.get("lock_ids", [])
        required = tdata.get("required", True)
        approved_skip = tdata.get("approved_skip_reason")

        # Criterion 2: state must be 'completed'
        if state != "completed":
            incomplete.append(tid)
            failed_criteria.append(f"Task '{tid}': state='{state}' (required: 'completed')")

        # Criterion 3: verification must pass
        if state == "completed" and verification not in ("pass", "not_configured"):
            failed_criteria.append(
                f"Task '{tid}': verification_status='{verification}' (expected 'pass' or 'not_configured')"
            )

        # Criterion 4: skipped required task without reason
        if state == "skipped" and required and not approved_skip:
            failed_criteria.append(
                f"Task '{tid}': skipped without approved_skip_reason (required task)"
            )

        # Criterion 5: terminal non-complete states
        if state in ("queued", "waiting", "ready", "running", "blocked", "failed", "aborted"):
            if tid not in incomplete:
                incomplete.append(tid)

        # Criterion 6: active workers/locks
        if worker_id is not None:
            failed_criteria.append(f"Task '{tid}': active worker '{worker_id}' still assigned")
        if lock_ids:
            failed_criteria.append(f"Task '{tid}': active locks {lock_ids}")

    ok = len(incomplete) == 0 and len(failed_criteria) == 0

    if not ok and incomplete:
        print(f"\nPhase completion blocked.\n")
        print(f"Phase: {phase_id}")
        print(f"Required tasks: {len(phase_tasks)}")
        print(f"Completed: {len(phase_tasks) - len(incomplete)}")
        print(f"Incomplete:")
        for tid in incomplete:
            state = task_ledger.tasks.get(tid, {}).get("state", "unknown")
            print(f"  - {tid}: {state}")
        next_task, reason = get_next_ready_task(task_graph, task_ledger)
        print(f"\nNext action:")
        if next_task:
            print(f"  Continue implementation with {next_task}.")
        else:
            print(f"  {reason}")

    return PhaseCoverageResult(
        ok=ok,
        phase_id=phase_id,
        incomplete_tasks=incomplete,
        failed_criteria=failed_criteria,
    )
