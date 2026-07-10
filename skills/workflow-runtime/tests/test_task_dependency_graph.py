# test_task_dependency_graph.py
"""
FEAT-050 — Task Dependency Graph Tests
Tests: 5 cases per blueprint
- Cycle detection blocks graph creation
- Unknown dependency reference blocks graph creation
- Correct dependency ordering
- Phase blocked when not all tasks complete
- Task graph JSON written correctly
"""
import pytest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from task_orchestrator import (
    build_task_graph, create_ledger_from_graph, load_task_ledger, write_task_ledger,
    validate_phase_completion, get_next_ready_task,
    CyclicDependencyError, UnknownDependencyError,
    TASK_GRAPH_PATH, TASK_LEDGER_PATH,
)


# Minimal plan JSON for testing
def _plan(feature_id, tasks, phases=None):
    return {
        "feature_id": feature_id,
        "phases": phases or [{"phase_id": "p1", "name": "Phase 1", "tasks": [t["task_id"] for t in tasks]}],
        "tasks": tasks,
    }


@pytest.fixture(autouse=True)
def tmp_state(tmp_path, monkeypatch):
    """Redirect state files to temp directory."""
    workflow_dir = tmp_path / ".agents" / "state" / "workflow"
    workflow_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("task_orchestrator._WORKFLOW_STATE_DIR", str(workflow_dir))
    monkeypatch.setattr("task_orchestrator.TASK_GRAPH_PATH", str(workflow_dir / "task_graph.json"))
    monkeypatch.setattr("task_orchestrator.TASK_LEDGER_PATH", str(workflow_dir / "tasks.json"))
    yield


def test_cycle_detection_blocks_graph():
    """TC-GRAPH-01: A cycle in task dependencies raises CyclicDependencyError."""
    plan = _plan("TEST-001", [
        {"task_id": "T1", "phase_id": "p1", "dependencies": ["T3"]},
        {"task_id": "T2", "phase_id": "p1", "dependencies": ["T1"]},
        {"task_id": "T3", "phase_id": "p1", "dependencies": ["T2"]},  # cycle: T1->T3->T2->T1
    ])
    with pytest.raises(CyclicDependencyError) as exc_info:
        build_task_graph(plan)
    assert "Cycle detected" in str(exc_info.value)


def test_unknown_dependency_reference_blocks_graph():
    """TC-GRAPH-02: A task referencing a non-existent dependency raises UnknownDependencyError."""
    plan = _plan("TEST-001", [
        {"task_id": "T1", "phase_id": "p1", "dependencies": []},
        {"task_id": "T2", "phase_id": "p1", "dependencies": ["T_NONEXISTENT"]},
    ])
    with pytest.raises(UnknownDependencyError) as exc_info:
        build_task_graph(plan)
    assert "T_NONEXISTENT" in str(exc_info.value)


def test_dependency_ordering_respected():
    """TC-GRAPH-03: Tasks with all deps completed appear in ready_queue; others do not."""
    plan = _plan("TEST-001", [
        {"task_id": "T1", "phase_id": "p1", "dependencies": []},
        {"task_id": "T2", "phase_id": "p1", "dependencies": ["T1"]},
        {"task_id": "T3", "phase_id": "p1", "dependencies": ["T2"]},
    ])
    graph = build_task_graph(plan)
    # Only T1 should be in ready_queue initially (no deps)
    assert "T1" in graph.ready_queue
    assert "T2" not in graph.ready_queue
    assert "T3" not in graph.ready_queue


def test_phase_blocked_when_task_incomplete():
    """TC-GRAPH-04: Phase is blocked when Task 1.1 is complete but 1.2/1.3 are not."""
    plan = {
        "feature_id": "TEST-001",
        "phases": [{"phase_id": "p1", "name": "Phase 1", "tasks": ["T1", "T2", "T3"]}],
        "tasks": [
            {"task_id": "T1", "phase_id": "p1", "dependencies": []},
            {"task_id": "T2", "phase_id": "p1", "dependencies": ["T1"]},
            {"task_id": "T3", "phase_id": "p1", "dependencies": ["T1"]},
        ],
    }
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)

    # Mark T1 as completed (with verification pass and no worker/lock)
    ledger.tasks["T1"]["state"] = "completed"
    ledger.tasks["T1"]["verification_status"] = "pass"
    ledger.tasks["T1"]["worker_id"] = None
    ledger.tasks["T1"]["lock_ids"] = []
    write_task_ledger(ledger)

    result = validate_phase_completion("p1", graph, ledger)
    assert result.ok is False
    assert "T2" in result.incomplete_tasks or "T3" in result.incomplete_tasks


def test_task_graph_json_written():
    """TC-GRAPH-05: build_task_graph writes task_graph.json with correct content."""
    plan = _plan("TEST-001", [
        {"task_id": "T1", "phase_id": "p1", "dependencies": []},
        {"task_id": "T2", "phase_id": "p1", "dependencies": ["T1"]},
    ])
    graph = build_task_graph(plan)

    import task_orchestrator as to
    written = json.loads(open(to.TASK_GRAPH_PATH, encoding="utf-8").read())
    assert written["feature_id"] == "TEST-001"
    assert "T1" in written["tasks"]
    assert "T2" in written["tasks"]
    assert written["ready_queue"] == ["T1"]
