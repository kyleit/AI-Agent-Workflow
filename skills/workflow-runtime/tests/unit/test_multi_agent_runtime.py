import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from multi_agent_runtime import AgentRegistry

def test_agent_registry():
    registry = AgentRegistry()
    registry.register_agent("Coder", ["writing_code"])
    assert "Coder" in registry.registry
    assert registry.handoff("Coder", "Reviewer") is False
