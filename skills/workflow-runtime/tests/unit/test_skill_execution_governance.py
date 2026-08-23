# test_skill_execution_governance.py
import pytest
import os
import sys
import shutil

# Add script directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from skill_router import SkillRouter
from evidence_gate_engine import EvidenceGateEngine

@pytest.fixture
def setup_docs_env(tmp_path):
    workspace = tmp_path / "governance_workspace"
    workspace.mkdir()
    
    # Create required doc folders
    os.makedirs(workspace / "docs" / "brainstorming", exist_ok=True)
    os.makedirs(workspace / "docs" / "planning", exist_ok=True)
    os.makedirs(workspace / "docs" / "blueprints", exist_ok=True)
    
    yield str(workspace)

def test_skill_router_load_and_route():
    # Test routing discovery phase to brainstorming skill
    router = SkillRouter()
    cfg = router.route_phase_to_skill("discovery")
    assert cfg is not None
    assert cfg["name"] == "brainstorming"
    
    # Test input requirements validation
    assert router.validate_inputs("brainstorming", {"feature_request": "extend_db", "project_context": "{}"}) is True
    assert router.validate_inputs("brainstorming", {"project_context": "{}"}) is False

def test_evidence_gate_governance_enforcement(setup_docs_env):
    workspace = setup_docs_env
    ge = EvidenceGateEngine(workspace_root=workspace)
    
    # Mode = autonomous (Enforced checks)
    evidence = {"workflow_mode": "autonomous", "plan_file": "plan.md", "profile_file": "profile.json"}
    
    # Initial state: docs/brainstorming/ has no .md files. Gate evaluation must return FAIL.
    assert ge.evaluate_gate("Gate1_PlanApproval", evidence) == "FAIL"
    
    # Add brainstorming file
    with open(os.path.join(workspace, "docs", "brainstorming", "FEAT-304.md"), "w") as f:
        f.write("# Brainstorming")
        
    # Still FAIL since plan file plan.md is not physically present in workspace root yet
    assert ge.evaluate_gate("Gate1_PlanApproval", evidence) == "BLOCKED"
    
    # Create plan and profile files
    with open(os.path.join(workspace, "plan.md"), "w") as f:
        f.write("# Plan\nPLAN APPROVED")
    with open(os.path.join(workspace, "profile.json"), "w") as f:
        f.write("{}")
        
    # Now it should PASS
    assert ge.evaluate_gate("Gate1_PlanApproval", evidence) == "PASS"

def test_evidence_gate_legacy_bypass(setup_docs_env):
    workspace = setup_docs_env
    ge = EvidenceGateEngine(workspace_root=workspace)
    
    # Mode = legacy (Bypassed folder validation check)
    evidence = {"workflow_mode": "legacy", "plan_file": "plan.md", "profile_file": "profile.json", "user_approved": True}
    
    # Create plan and profile files (no docs/ folder artifacts created)
    with open(os.path.join(workspace, "plan.md"), "w") as f:
        f.write("# Plan")
    with open(os.path.join(workspace, "profile.json"), "w") as f:
        f.write("{}")
        
    # Since workflow_mode=legacy, it bypasses physical docs checks and evaluates directly using approval flag
    assert ge.evaluate_gate("Gate1_PlanApproval", evidence) == "PASS"
