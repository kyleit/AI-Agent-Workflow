import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from policy_approval_safety_runtime import PolicyEnforcementEngine

def test_policy_path_and_cmd_safety():
    engine = PolicyEnforcementEngine(workspace_root=".")
    
    # Path boundary test
    assert engine.is_path_safe("skills/workflow-runtime") is True
    assert engine.is_path_safe("C:/Windows/System32") is False
    
    # Command safety test
    assert engine.is_command_safe("pytest tests/") is True
    assert engine.is_command_safe("rm -rf /") is False
