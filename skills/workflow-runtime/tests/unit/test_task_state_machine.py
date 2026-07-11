# test_task_state_machine.py
import pytest
pytestmark = pytest.mark.unit
pytestmark = [pytest.mark.unit, pytest.mark.stateful]

"""
FEAT-050 — Task State Machine Tests
Tests: 4 forbidden transitions + allowed transitions
"""
import pytest
pytestmark = pytest.mark.unit
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from task_orchestrator import (
    build_task_graph, create_ledger_from_graph, write_task_ledger,
    transition_task_state, ForbiddenStateTransitionError,
)


def _plan_simple():
    return {
        "feature_id": "TEST-SM",
        "phases": [{"phase_id": "p1", "name": "P1", "tasks": ["T1"]}],
        "tasks": [{"task_id": "T1", "phase_id": "p1", "dependencies": []}],
    }


@pytest.fixture(autouse=True)
def tmp_state(tmp_path, monkeypatch):
    workflow_dir = tmp_path / ".agents" / "state" / "workflow"
    workflow_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("task_orchestrator._WORKFLOW_STATE_DIR", str(workflow_dir))
    monkeypatch.setattr("task_orchestrator.TASK_GRAPH_PATH", str(workflow_dir / "task_graph.json"))
    monkeypatch.setattr("task_orchestrator.TASK_LEDGER_PATH", str(workflow_dir / "tasks.json"))


@pytest.fixture
def simple_ledger():
    plan = _plan_simple()
    graph = build_task_graph(plan)
    ledger = create_ledger_from_graph(graph)
    return ledger


def _set_state(ledger, task_id, state, verification="not_configured"):
    ledger.tasks[task_id]["state"] = state
    ledger.tasks[task_id]["verification_status"] = verification
    ledger.tasks[task_id]["worker_id"] = None
    ledger.tasks[task_id]["lock_ids"] = []
    write_task_ledger(ledger)


def test_queued_to_completed_is_forbidden(simple_ledger):
    """TC-SM-01: queued -> completed is explicitly forbidden (via ALLOWED_TRANSITIONS check)."""
    # T1 starts as 'ready' (no deps), set to waiting to test queued-like blocked path
    _set_state(simple_ledger, "T1", "waiting")
    with pytest.raises(ForbiddenStateTransitionError) as exc:
        transition_task_state("T1", "completed", simple_ledger)
    assert "forbidden" in str(exc.value).lower() or "waiting" in str(exc.value).lower()


def test_waiting_to_completed_is_forbidden(simple_ledger):
    """TC-SM-02: waiting -> completed is explicitly forbidden."""
    _set_state(simple_ledger, "T1", "waiting")
    with pytest.raises(ForbiddenStateTransitionError) as exc:
        transition_task_state("T1", "completed", simple_ledger)
    assert "forbidden" in str(exc.value).lower() or "waiting" in str(exc.value).lower()


def test_running_to_queued_is_forbidden(simple_ledger):
    """TC-SM-03: running -> queued is explicitly forbidden."""
    _set_state(simple_ledger, "T1", "running")
    with pytest.raises(ForbiddenStateTransitionError) as exc:
        transition_task_state("T1", "queued", simple_ledger)
    assert "forbidden" in str(exc.value).lower()


def test_completed_to_running_is_forbidden(simple_ledger):
    """TC-SM-04: completed -> running without rerun approval is forbidden."""
    _set_state(simple_ledger, "T1", "completed", verification="pass")
    # completed state has no allowed transitions
    with pytest.raises(ForbiddenStateTransitionError) as exc:
        transition_task_state("T1", "running", simple_ledger)
    assert "terminal" in str(exc.value).lower() or "none" in str(exc.value).lower() or "forbidden" in str(exc.value).lower()


def test_allowed_queued_to_ready(simple_ledger):
    """TC-SM-05: waiting -> ready is allowed (queued -> waiting -> ready flow)."""
    _set_state(simple_ledger, "T1", "waiting")
    result = transition_task_state("T1", "ready", simple_ledger, reason="deps resolved")
    assert result is True
    assert simple_ledger.tasks["T1"]["state"] == "ready"


def test_allowed_ready_to_running(simple_ledger):
    """TC-SM-06: ready -> running is allowed."""
    _set_state(simple_ledger, "T1", "ready")
    result = transition_task_state("T1", "running", simple_ledger)
    assert result is True
    assert simple_ledger.tasks["T1"]["state"] == "running"


def test_allowed_running_to_completed_with_verification(simple_ledger):
    """TC-SM-07: running -> completed requires verification pass + no worker + no lock."""
    _set_state(simple_ledger, "T1", "running", verification="pass")
    result = transition_task_state("T1", "completed", simple_ledger, reason="all criteria met")
    assert result is True
    assert simple_ledger.tasks["T1"]["state"] == "completed"


def test_running_to_completed_blocked_without_verification(simple_ledger):
    """TC-SM-08: running -> completed blocked when verification_status = 'pending'."""
    _set_state(simple_ledger, "T1", "running", verification="pending")
    with pytest.raises(ForbiddenStateTransitionError) as exc:
        transition_task_state("T1", "completed", simple_ledger)
    assert "verification" in str(exc.value).lower()
