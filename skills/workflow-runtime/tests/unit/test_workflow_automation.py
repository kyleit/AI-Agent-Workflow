# test_workflow_automation.py
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
def setup_state_dir(tmp_path):
    # Setup tmp workspace structure
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    
    # Create required subdirs
    agents_state = workspace / ".agents" / "state"
    agents_state.mkdir(parents=True)
    
    yield str(workspace)

def test_workflow_state_machine_init_and_transition(setup_state_dir):
    sm = WorkflowStateMachine(workspace_root=setup_state_dir)
    assert sm.current_state == "Brainstorming"
    
    # Transition to planning
    sm.transition_to("Planning")
    assert sm.current_state == "Planning"
    assert sm.history == ["Brainstorming"]
    
    # Verify snapshot file exists
    assert os.path.exists(sm.snapshot_file)
    with open(sm.snapshot_file, "r") as f:
        data = json.load(f)
        assert data["current_state"] == "Planning"

def test_evidence_gate_engine_evaluations(setup_state_dir):
    ge = EvidenceGateEngine(workspace_root=setup_state_dir)
    
    # Prepare files in temp workspace
    plan_file = "implementation_plan.md"
    profile_file = "project-profile.json"
    
    plan_path = os.path.join(setup_state_dir, plan_file)
    profile_path = os.path.join(setup_state_dir, profile_file)
    
    # Gate 1 is BLOCKED if files don't exist
    decision = ge.evaluate_gate("Gate1_PlanApproval", {"plan_file": plan_file, "profile_file": profile_file})
    assert decision == "BLOCKED"
    
    # Create empty files
    with open(plan_path, "w") as f:
        f.write("# Plan\n")
    with open(profile_path, "w") as f:
        f.write("{}")
        
    # Gate 1 is FAIL if no approval keyword
    decision = ge.evaluate_gate("Gate1_PlanApproval", {"plan_file": plan_file, "profile_file": profile_file})
    assert decision == "FAIL"
    
    # Gate 1 passes with keyword or user_approved flag
    decision = ge.evaluate_gate("Gate1_PlanApproval", {
        "plan_file": plan_file,
        "profile_file": profile_file,
        "user_approved": True
    })
    assert decision == "PASS"

def test_auto_transition_controller_loop(setup_state_dir):
    sm = WorkflowStateMachine(workspace_root=setup_state_dir)
    ge = EvidenceGateEngine(workspace_root=setup_state_dir)
    controller = AutoTransitionController(sm, ge)
    
    # Set starting state to Implementation (which is in auto phases list)
    sm.transition_to("Implementation")
    
    # Compilation success advances Implementation to Debug
    next_state = controller.run_auto_lifecycle({"compilation_success": True})
    assert next_state == "Debug"
    assert sm.current_state == "Debug"
    
    # Test pass advances Debug to Verification
    next_state = controller.run_auto_lifecycle({"tests_passed": True})
    assert next_state == "Verification"
    assert sm.current_state == "Verification"

def test_rollback_policy_requires_explicit_approval(setup_state_dir):
    sm = WorkflowStateMachine(workspace_root=setup_state_dir)
    report = sm.request_rollback("Memory leak detected")
    assert "WAITING_FOR_APPROVAL" in report
    
    # Executing rollback without approval raises WorkflowStateError
    with pytest.raises(WorkflowStateError):
        sm.execute_rollback()
        
    # Once approved, rollback is executed successfully
    sm.rollback_approved = True
    success = sm.execute_rollback()
    assert success is True
    assert sm.current_state == "Implementation"
