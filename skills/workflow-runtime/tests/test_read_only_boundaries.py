import os
import pytest
from permission_boundary import PermissionBoundary, Permission, PermissionError
from state_store import get_state_store

def test_read_only_boundary_in_brainstorming(isolated_workspace):
    # Set phase to brainstorming
    store = get_state_store()
    workflow = store.get("workflow") or {}
    workflow["active_phase"] = "brainstorming"
    store.set("workflow", workflow)
    
    boundary = PermissionBoundary()
    perm = Permission(
        owner_type="agent",
        owner_id="coder",
        scope=["*"],
        capabilities=["execute", "write"]
    )
    
    # Writing to a code file during brainstorming should raise PermissionError
    with pytest.raises(PermissionError, match="blocked during the read-only phase"):
        boundary.check_tool_access(perm, "write", "skills/workflow-runtime/scripts/workflow_runtime.py")
        
    # Writing to scratch or docs during brainstorming is allowed
    # (should not raise read-only phase error, might raise scope error if scope is not '*')
    boundary.check_tool_access(perm, "write", "docs/brainstorming/FEAT-999.md")

def test_write_allowed_in_implementation(isolated_workspace):
    # Set phase to implementation
    store = get_state_store()
    workflow = store.get("workflow") or {}
    workflow["active_phase"] = "implementation"
    store.set("workflow", workflow)
    
    boundary = PermissionBoundary()
    perm = Permission(
        owner_type="agent",
        owner_id="coder",
        scope=["*"],
        capabilities=["execute", "write"]
    )
    
    # Writing to a code file should succeed without read-only phase block
    boundary.check_tool_access(perm, "write", "skills/workflow-runtime/scripts/workflow_runtime.py")
