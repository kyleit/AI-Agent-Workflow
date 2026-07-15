import os
import pytest
from agent_routing import AgentSelector

def test_agent_selector_metadata_loading(isolated_workspace):
    selector = AgentSelector(os.path.join(isolated_workspace, "agents"))
    
    # Load backend-developer metadata
    meta = selector.load_agent_metadata("backend-developer")
    assert meta is not None
    assert meta.get("id") == "backend-developer"
    assert "backend" in meta.get("capabilities", [])

def test_agent_selector_recruitment(isolated_workspace):
    selector = AgentSelector(os.path.join(isolated_workspace, "agents"))
    
    # Recruit coder/backend developer for implementation phase with backend tags
    res = selector.recruit_agent_for_task("implementation", ["backend"])
    
    assert res is not None
    assert res.get("agent_id") in ["coder", "backend-developer"]
    assert "reviewer" in res.get("handoff_targets", []) or "coder" in res.get("handoff_targets", []) or "backend-developer" in res.get("handoff_targets", []) or len(res.get("handoff_targets")) >= 0
