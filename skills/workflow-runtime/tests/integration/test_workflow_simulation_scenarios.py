# test_workflow_simulation_scenarios.py
import pytest
import os
import sys
import json
import shutil

# Add script directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from workflow_state_machine import WorkflowStateMachine, WorkflowStateError
from evidence_gate_engine import EvidenceGateEngine
from auto_transition_controller import AutoTransitionController

@pytest.fixture
def setup_workspaces(tmp_path):
    ws1 = tmp_path / "ws1"
    ws1.mkdir()
    os.makedirs(ws1 / ".agents" / "state", exist_ok=True)
    
    ws2 = tmp_path / "ws2"
    ws2.mkdir()
    os.makedirs(ws2 / ".agents" / "state", exist_ok=True)
    
    yield str(ws1), str(ws2)

def test_crash_recovery_and_resume(setup_workspaces):
    ws1, _ = setup_workspaces
    
    # 1. State machine starts at Brainstorming and moves to Planning
    sm = WorkflowStateMachine(workspace_root=ws1)
    sm.transition_to("Planning")
    assert sm.current_state == "Planning"
    
    # Verify snapshot file has been written
    assert os.path.exists(sm.snapshot_file)
    
    # 2. Simulate Orchestrator Crash (destroy current sm object)
    del sm
    
    # 3. Restore state by initializing a new sm instance loading from the same directory
    sm_new = WorkflowStateMachine(workspace_root=ws1)
    assert sm_new.current_state == "Planning"
    assert sm_new.history == ["Brainstorming"]

def test_failed_agent_retry_handling(setup_workspaces):
    ws1, _ = setup_workspaces
    sm = WorkflowStateMachine(workspace_root=ws1)
    ge = EvidenceGateEngine(workspace_root=ws1)
    controller = AutoTransitionController(sm, ge)
    
    sm.transition_to("Implementation")
    
    # If compilation fails, state must NOT advance and should remain at Implementation
    state = controller.run_auto_lifecycle({"compilation_success": False})
    assert state == "Implementation"
    assert sm.current_state == "Implementation"

def test_evidence_corruption_handling(setup_workspaces):
    ws1, _ = setup_workspaces
    ge = EvidenceGateEngine(workspace_root=ws1)
    
    # Plan files corrupted (e.g. empty file)
    plan_file = "implementation_plan.md"
    profile_file = "project-profile.json"
    plan_path = os.path.join(ws1, plan_file)
    profile_path = os.path.join(ws1, profile_file)
    
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write("")  # Corrupted / empty plan
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write("")
        
    decision = ge.evaluate_gate("Gate1_PlanApproval", {"plan_file": plan_file, "profile_file": profile_file})
    assert decision == "FAIL"

def test_concurrent_workflow_isolation(setup_workspaces):
    ws1, ws2 = setup_workspaces
    
    # Initialize two parallel state machines
    sm1 = WorkflowStateMachine(workspace_root=ws1)
    sm2 = WorkflowStateMachine(workspace_root=ws2)
    
    # Move sm1 to Implementation, sm2 stays at Brainstorming
    sm1.transition_to("Planning")
    sm1.transition_to("ArchitectureReview")
    sm1.transition_to("Blueprint")
    sm1.transition_to("Implementation")
    
    assert sm1.current_state == "Implementation"
    assert sm2.current_state == "Brainstorming"
    
    # Verify their snapshot files are completely isolated
    with open(sm1.snapshot_file, "r") as f:
        data1 = json.load(f)
        assert data1["current_state"] == "Implementation"
        
    with open(sm2.snapshot_file, "r") as f:
        data2 = json.load(f)
        assert data2["current_state"] == "Brainstorming"
