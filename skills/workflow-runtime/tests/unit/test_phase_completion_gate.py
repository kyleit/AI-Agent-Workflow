# test_phase_completion_gate.py
import pytest
pytestmark = pytest.mark.unit

"""
FEAT-050 — Phase Completion Gate Tests
3 test cases:
1. Phase 1 incomplete with only Task 1.1 done
2. Phase 1 complete only when ALL tasks done
3. Skipped required task without approved_skip_reason blocks completion
"""
import pytest
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from task_orchestrator import (
    build_task_graph, create_ledger_from_graph, write_task_ledger,
    validate_phase_completion,
)


def _plan_p1():
    return {
        "feature_id": "TEST-PHASE",
        "phases": [{"phase_id": "p1", "name": "Phase 1", "tasks": ["T1", "T2", "T3"]}],
        "tasks": [
            {"task_id": "T1", "phase_id": "p1", "dependencies": []},
            {"task_id": "T2", "phase_id": "p1", "dependencies": ["T1"]},
            {"task_id": "T3", "phase_id": "p1", "dependencies": ["T1"]},
        ],
    }


@pytest.fixture(autouse=True)
def tmp_state(tmp_path, monkeypatch):
    workflow_dir = tmp_path / ".agents" / "state" / "workflow"
    workflow_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("task_orchestrator._WORKFLOW_STATE_DIR", str(workflow_dir))
    monkeypatch.setattr("task_orchestrator.TASK_GRAPH_PATH", str(workflow_dir / "task_graph.json"))
    monkeypatch.setattr("task_orchestrator.TASK_LEDGER_PATH", str(workflow_dir / "tasks.json"))


def _complete_task(ledger, task_id):
    ledger.tasks[task_id]["state"] = "completed"
    ledger.tasks[task_id]["verification_status"] = "pass"
    ledger.tasks[task_id]["worker_id"] = None
    ledger.tasks[task_id]["lock_ids"] = []


def test_phase_incomplete_with_only_first_task_done():
    """TC-PHASE-01: Phase 1 is NOT complete when only T1 is done (hard rule)."""
    plan = _plan_p1()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)

    _complete_task(ledger, "T1")
    write_task_ledger(ledger)

    result = validate_phase_completion("p1", graph, ledger)
    assert result.ok is False
    assert len(result.incomplete_tasks) >= 2, \
        f"Expected 2 incomplete tasks (T2, T3), got: {result.incomplete_tasks}"
    assert "T2" in result.incomplete_tasks or "T3" in result.incomplete_tasks


def test_phase_complete_only_when_all_tasks_done():
    """TC-PHASE-02: Phase 1 is complete when ALL tasks (T1, T2, T3) are completed with verification."""
    plan = _plan_p1()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)

    _complete_task(ledger, "T1")
    _complete_task(ledger, "T2")
    _complete_task(ledger, "T3")
    write_task_ledger(ledger)

    result = validate_phase_completion("p1", graph, ledger)
    assert result.ok is True, f"Phase should be complete. Failures: {result.failed_criteria}"


def test_skipped_required_task_blocks_without_reason():
    """TC-PHASE-03: Skipped required task without approved_skip_reason blocks phase completion."""
    plan = _plan_p1()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)

    _complete_task(ledger, "T1")
    _complete_task(ledger, "T2")
    # T3: skipped without approved_skip_reason
    ledger.tasks["T3"]["state"] = "skipped"
    ledger.tasks["T3"]["required"] = True
    ledger.tasks["T3"]["approved_skip_reason"] = None
    write_task_ledger(ledger)

    result = validate_phase_completion("p1", graph, ledger)
    assert result.ok is False
    # Check that the failure is about skipped without reason
    criteria_str = " ".join(result.failed_criteria)
    assert "skip" in criteria_str.lower() or "T3" in criteria_str


def test_active_worker_blocks_completion():
    """TC-PHASE-04: A task with active worker cannot be marked complete."""
    plan = _plan_p1()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)

    _complete_task(ledger, "T1")
    _complete_task(ledger, "T2")
    _complete_task(ledger, "T3")
    # Simulate active worker on T3
    ledger.tasks["T3"]["worker_id"] = "worker-123"
    write_task_ledger(ledger)

    result = validate_phase_completion("p1", graph, ledger)
    assert result.ok is False
    criteria_str = " ".join(result.failed_criteria)
    assert "worker" in criteria_str.lower()
