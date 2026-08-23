# test_workflow_supervisor.py
import pytest
import os
import sys
import json
import time

# Add script directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from workflow_supervisor import WorkflowSupervisor
from agent_dispatcher import AgentDispatcher

@pytest.fixture
def setup_workspace(tmp_path):
    workspace = tmp_path / "supervisor_workspace"
    workspace.mkdir()
    os.makedirs(workspace / ".agents" / "state", exist_ok=True)
    os.makedirs(workspace / ".agents" / "config", exist_ok=True)
    
    # Save a mock registry config
    registry = {
      "brainstorming": {
        "skill": "brainstorming",
        "agent": "brainstorm-agent",
        "next": "Planning",
        "evidence": []
      },
      "planning": {
        "skill": "planning",
        "agent": "planning-agent",
        "next": "Gate1_PlanApproval",
        "evidence": ["implementation_plan.md"]
      }
    }
    reg_path = workspace / ".agents" / "config" / "phase_registry.json"
    with open(reg_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)
        
    yield str(workspace), str(reg_path)

def test_agent_dispatcher_concurrency_limit():
    dispatcher = AgentDispatcher(max_workers=2)
    
    # Block target thread wrapper
    def slow_task():
        time.sleep(0.5)
        
    # Dispatch first two agents successfully
    assert dispatcher.dispatch_agent("agent-1", slow_task) is True
    assert dispatcher.dispatch_agent("agent-2", slow_task) is True
    
    # Third agent must be blocked
    assert dispatcher.dispatch_agent("agent-3", slow_task) is False
    assert dispatcher.get_active_count() == 2

def test_workflow_supervisor_steps(setup_workspace):
    workspace, reg_path = setup_workspace
    supervisor = WorkflowSupervisor(workspace_root=workspace, registry_path=reg_path)
    
    # Starts at Brainstorming -> moves to Planning automatically
    state = supervisor.run_supervisor_step({})
    assert state == "Planning"
    assert "Phase Brainstorming execution completed" in supervisor.notifications[0]
    
    # Moves to Gate1_PlanApproval automatically
    state = supervisor.run_supervisor_step({})
    assert state == "Gate1_PlanApproval"
    
    # Gate 1 should block without files
    state = supervisor.run_supervisor_step({"plan_file": "plan.md", "profile_file": "profile.json"})
    assert state == "Gate1_PlanApproval"
    assert "blocked" in supervisor.notifications[-1]
    
    # Pass Gate 1 when approved
    plan_path = os.path.join(workspace, "plan.md")
    profile_path = os.path.join(workspace, "profile.json")
    with open(plan_path, "w") as f:
        f.write("# Plan\n")
    with open(profile_path, "w") as f:
        f.write("{}")
        
    state = supervisor.run_supervisor_step({
        "plan_file": "plan.md",
        "profile_file": "profile.json",
        "user_approved": True
    })
    assert state == "ArchitectureReview"
    assert "approved" in supervisor.notifications[-1]
