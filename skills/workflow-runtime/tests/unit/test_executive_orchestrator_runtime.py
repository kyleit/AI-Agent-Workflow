import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from executive_orchestrator_runtime import ExecutiveOrchestratorRuntimeModule

def test_executive_loop_state_machine(tmp_path):
    snapshot_file = tmp_path / "context_snapshot.json"
    module = ExecutiveOrchestratorRuntimeModule(session_path=str(snapshot_file))
    
    assert module.state == "STANDBY"
    assert module.execution_mode == "PROGRAM"
    module.initialize()
    assert module.state == "ACTIVE"
    
    module.transition_to("COMPLETED")
    assert module.state == "COMPLETED"
    
    with pytest.raises(ValueError):
        module.transition_to("ACTIVE") # Invalid transition direct from COMPLETED

def test_continuous_execution_mode(tmp_path):
    snapshot_file = tmp_path / "context_snapshot.json"
    module = ExecutiveOrchestratorRuntimeModule(session_path=str(snapshot_file))
    
    # Defaults to PROGRAM mode
    assert module.should_continue_automatically("PASS") is True
    assert module.should_continue_automatically("FAIL") is False
    
    # Change to STEP mode
    module.execution_mode = "STEP"
    assert module.should_continue_automatically("PASS") is False

