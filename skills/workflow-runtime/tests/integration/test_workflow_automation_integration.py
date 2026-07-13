# test_workflow_automation_integration.py
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
from post_release_lifecycle import PostReleaseLifecycleAutomator

@pytest.fixture
def setup_workspace(tmp_path):
    workspace = tmp_path / "wf_workspace"
    workspace.mkdir()
    
    # Create required subdirs
    agents_state = workspace / ".agents" / "state"
    agents_state.mkdir(parents=True)
    
    reviews_dir = workspace / "docs" / "reviews"
    reviews_dir.mkdir(parents=True)
    
    yield str(workspace)

def test_end_to_end_workflow_gates_and_transitions(setup_workspace):
    # 1. Initialize State Machine and Gate Engine
    sm = WorkflowStateMachine(workspace_root=setup_workspace)
    ge = EvidenceGateEngine(workspace_root=setup_workspace)
    controller = AutoTransitionController(sm, ge)
    
    assert sm.current_state == "Brainstorming"
    
    # 2. Move to Planning
    sm.transition_to("Planning")
    assert sm.current_state == "Planning"
    
    # Prepare files for Gate 1: Planning Approval
    plan_file = "implementation_plan.md"
    profile_file = "project-profile.json"
    
    plan_path = os.path.join(setup_workspace, plan_file)
    profile_path = os.path.join(setup_workspace, profile_file)
    
    # Gate 1 should block if files are missing
    decision = ge.evaluate_gate("Gate1_PlanApproval", {"plan_file": plan_file, "profile_file": profile_file})
    assert decision == "BLOCKED"
    
    # Create the files
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write("# Plan\n")
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write("{}")
        
    # Gate 1 fails without explicit approval
    decision = ge.evaluate_gate("Gate1_PlanApproval", {"plan_file": plan_file, "profile_file": profile_file})
    assert decision == "FAIL"
    
    # Approve Gate 1
    decision = ge.evaluate_gate("Gate1_PlanApproval", {
        "plan_file": plan_file,
        "profile_file": profile_file,
        "user_approved": True
    })
    assert decision == "PASS"
    
    # 3. Transition to ArchitectureReview and Blueprint
    sm.transition_to("ArchitectureReview")
    sm.transition_to("Blueprint")
    
    # Prepare files for Gate 2: Blueprint Approval
    bp_file = "technical_blueprint.md"
    bp_path = os.path.join(setup_workspace, bp_file)
    
    decision = ge.evaluate_gate("Gate2_BlueprintApproval", {"blueprint_file": bp_file})
    assert decision == "BLOCKED"
    
    with open(bp_path, "w", encoding="utf-8") as f:
        f.write("# Blueprint\n")
        
    decision = ge.evaluate_gate("Gate2_BlueprintApproval", {"blueprint_file": bp_file})
    assert decision == "FAIL"
    
    decision = ge.evaluate_gate("Gate2_BlueprintApproval", {
        "blueprint_file": bp_file,
        "user_approved": True
    })
    assert decision == "PASS"
    
    # 4. Transition to Implementation and run Auto Transition Controller
    sm.transition_to("Implementation")
    
    # Compilation success -> Debug
    state = controller.run_auto_lifecycle({"compilation_success": True})
    assert state == "Debug"
    
    # Tests pass -> Verification
    state = controller.run_auto_lifecycle({"tests_passed": True})
    assert state == "Verification"
    
    # Compliance passes -> Certification
    state = controller.run_auto_lifecycle({"compliance_passed": True})
    assert state == "Certification"
    
    # Stress tests pass without leaks -> FinalReview
    state = controller.run_auto_lifecycle({"stress_passed": True, "resource_leaks": False})
    assert state == "FinalReview"
    
    # Completeness passes -> ReleasePreparation
    state = controller.run_auto_lifecycle({"completeness_passed": True})
    assert state == "ReleasePreparation"
    
    # 5. Gate 3: Release Approval
    rc_file = "release_candidate_report.md"
    log_file = "tests.log"
    rc_path = os.path.join(setup_workspace, rc_file)
    log_path = os.path.join(setup_workspace, log_file)
    
    decision = ge.evaluate_gate("Gate3_ReleaseApproval", {"release_candidate_file": rc_file, "test_log_file": log_file})
    assert decision == "BLOCKED"
    
    with open(rc_path, "w", encoding="utf-8") as f:
        f.write("# Release Candidate\n")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("All 61 passed\n")
        
    decision = ge.evaluate_gate("Gate3_ReleaseApproval", {"release_candidate_file": rc_file, "test_log_file": log_file})
    assert decision == "FAIL"
    
    decision = ge.evaluate_gate("Gate3_ReleaseApproval", {
        "release_candidate_file": rc_file,
        "test_log_file": log_file,
        "user_approved": True
    })
    assert decision == "PASS"
    
    # 6. Execute Release and run post-release lifecycle automation
    sm.transition_to("ReleaseExecution")
    
    # Run post-release lifecycle automator
    out_dir = os.path.join(setup_workspace, "docs", "reviews")
    automator = PostReleaseLifecycleAutomator(
        release_version="6.14.2",
        git_commit="1f7f0e7",
        output_dir=out_dir
    )
    reports = automator.run_all_phases()
    
    # Validate generated reports existence
    assert os.path.exists(reports["post_release_validation"])
    assert os.path.exists(reports["production_monitoring"])
    assert os.path.exists(reports["maintenance_status"])
    assert os.path.exists(reports["runtime_governance"])
    assert os.path.exists(reports["continuous_improvement"])
    assert os.path.exists(reports["operational_maturity_assessment"])
    assert os.path.exists(reports["runtime_roadmap"])
