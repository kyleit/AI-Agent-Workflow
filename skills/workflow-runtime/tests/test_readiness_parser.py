import os
import pytest
from confidence_gate import ClarificationGate, ClarificationGateException
from state_store import get_state_store

def test_clarification_gate_blocked(isolated_workspace):
    gate = ClarificationGate(isolated_workspace)
    
    # Check score below 85.0 blocks and sets status to BLOCKED
    with pytest.raises(ClarificationGateException) as excinfo:
        gate.check_readiness_and_route("brainstorming", 80.0, ["Missing Scope Boundary"])
        
    assert "below 85.0" in str(excinfo.value)
    assert excinfo.value.gaps == ["Missing Scope Boundary"]
    
    store = get_state_store()
    workflow = store.get("workflow")
    assert workflow.get("status") == "BLOCKED"
    assert workflow.get("active_phase") == "brainstorming"

def test_clarification_gate_success(isolated_workspace):
    gate = ClarificationGate(isolated_workspace)
    
    res = gate.check_readiness_and_route("brainstorming", 90.0, [])
    assert res["status"] == "success"
    assert res["phase"] == "planning"
    
    store = get_state_store()
    workflow = store.get("workflow")
    assert workflow.get("status") == "success"
    assert workflow.get("active_phase") == "planning"
