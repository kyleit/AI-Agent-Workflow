# test_next_ready_task.py
"""
FEAT-050 — Next-Task Recommendation Tests
4 scenarios:
1. After T1 complete -> next is T2
2. Does NOT recommend next phase while current phase incomplete
3. Does NOT recommend debug while current phase incomplete
4. Does NOT recommend release before all phases + debug + verify
"""
import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from task_orchestrator import (
    build_task_graph, create_ledger_from_graph, write_task_ledger,
    get_next_ready_task,
)


def _plan_two_phase():
    return {
        "feature_id": "TEST-NEXT",
        "phases": [
            {"phase_id": "p1", "name": "Phase 1", "tasks": ["T1", "T2", "T3"]},
            {"phase_id": "p2", "name": "Phase 2", "tasks": ["T4"]},
        ],
        "tasks": [
            {"task_id": "T1", "phase_id": "p1", "dependencies": []},
            {"task_id": "T2", "phase_id": "p1", "dependencies": ["T1"]},
            {"task_id": "T3", "phase_id": "p1", "dependencies": ["T1"]},
            {"task_id": "T4", "phase_id": "p2", "dependencies": ["T2", "T3"]},
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
    write_task_ledger(ledger)
    # Update graph ready_queue
    return ledger


def test_after_t1_complete_next_is_t2_or_t3():
    """TC-NEXT-01: After T1 complete, next recommendation is T2 or T3 (both ready)."""
    plan = _plan_two_phase()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)
    ledger.current_phase = "p1"
    write_task_ledger(ledger)

    # Complete T1
    _complete_task(ledger, "T1")
    # Update graph's ready_queue to include T2, T3
    graph.ready_queue = ["T2", "T3"]
    graph.tasks["T2"].state = "ready"
    graph.tasks["T3"].state = "ready"
    graph.tasks["T2"].dependencies = ["T1"]
    graph.tasks["T3"].dependencies = ["T1"]
    ledger.tasks["T2"]["state"] = "ready"
    ledger.tasks["T3"]["state"] = "ready"
    write_task_ledger(ledger)

    next_task, reason = get_next_ready_task(graph, ledger)
    assert next_task in ("T2", "T3"), f"Expected T2 or T3, got {next_task}: {reason}"


def test_does_not_recommend_next_phase_while_p1_incomplete():
    """TC-NEXT-02: Does NOT recommend T4 (phase 2) while p1 is incomplete."""
    plan = _plan_two_phase()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)
    ledger.current_phase = "p1"
    write_task_ledger(ledger)

    # Complete only T1 (T2, T3 still queued)
    _complete_task(ledger, "T1")

    next_task, reason = get_next_ready_task(graph, ledger)
    assert next_task != "T4", f"Should NOT recommend T4 while p1 incomplete. Got: {next_task}: {reason}"


def test_does_not_recommend_debug_while_phase_incomplete():
    """TC-NEXT-03: When tasks remain in current phase, next is a task, not debug."""
    plan = _plan_two_phase()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)
    ledger.current_phase = "p1"
    write_task_ledger(ledger)

    # Only T1 is ready, nothing else done
    next_task, reason = get_next_ready_task(graph, ledger)
    # Should return T1, not debug
    assert next_task == "T1"
    assert "debug" not in reason.lower(), f"Should not mention debug yet. Got: {reason}"


def test_does_not_recommend_release_prematurely():
    """TC-NEXT-04: Never recommends /release before all phases + debug + verify complete."""
    plan = _plan_two_phase()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)
    ledger.current_phase = "p1"
    write_task_ledger(ledger)

    # Even if T1 done, p1 incomplete -> no release
    _complete_task(ledger, "T1")

    next_task, reason = get_next_ready_task(graph, ledger)
    assert "release" not in reason.lower(), f"Should not mention release. Got: {reason}"
    # next_task should not be None from ready_queue recommending release phase
    assert next_task != "release"
