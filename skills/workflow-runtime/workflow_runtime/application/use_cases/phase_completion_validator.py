"""
workflow_runtime/application/use_cases/phase_completion_validator.py

Phase completion validator and task dependency state verifier.
"""
from __future__ import annotations

import os
from typing import Any, cast

from workflow_runtime.application.use_cases.task_models import (
    PhaseCoverageResult, TaskGraph, TaskLedger)

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
    """
    phase_info = task_graph.phases.get(phase_id)
    if phase_info is None:
        return PhaseCoverageResult(
            ok=False,
            phase_id=phase_id,
            failed_criteria=[f"Phase '{phase_id}' not found in task graph."],
        )

    phase_tasks: list[Any] = cast(list[Any], phase_info.get("tasks", [])) if isinstance(phase_info.get("tasks"), list) else []
    incomplete: list[str] = []
    failed_criteria: list[str] = []

    for tid in phase_tasks:
        tdata = task_ledger.tasks.get(tid)
        if tdata is None:
            incomplete.append(tid)
            failed_criteria.append(f"Task '{tid}' missing from ledger (LedgerConsistencyError)")
            continue

        state = tdata.get("state", "queued")
        verification = tdata.get("verification_status", "pending")
        worker_id = tdata.get("worker_id")
        lock_ids: list[Any] = cast(list[Any], tdata.get("lock_ids", [])) if isinstance(tdata.get("lock_ids"), list) else []
        required = tdata.get("required", True)
        approved_skip = tdata.get("approved_skip_reason")

        if state != "completed":
            incomplete.append(tid)
            failed_criteria.append(f"Task '{tid}': state='{state}' (required: 'completed')")

        if state == "completed" and verification not in ("pass", "not_configured"):
            failed_criteria.append(
                f"Task '{tid}': verification_status='{verification}' (expected 'pass' or 'not_configured')"
            )

        if state == "skipped" and required and not approved_skip:
            failed_criteria.append(
                f"Task '{tid}': skipped without approved_skip_reason (required task)"
            )

        if state in ("queued", "waiting", "ready", "running", "blocked", "failed", "aborted"):
            if tid not in incomplete:
                incomplete.append(tid)

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

    return PhaseCoverageResult(
        ok=ok,
        phase_id=phase_id,
        incomplete_tasks=incomplete,
        failed_criteria=failed_criteria,
    )


__all__ = [
    "VALID_STATES",
    "ALLOWED_TRANSITIONS",
    "FORBIDDEN_SHORTCUTS",
    "TASK_GRAPH_PATH",
    "TASK_LEDGER_PATH",
    "validate_phase_completion",
]
