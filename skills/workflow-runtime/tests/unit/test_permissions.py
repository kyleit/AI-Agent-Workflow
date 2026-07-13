# test_permissions.py
import pytest
import os
import sys
import time

# Add script directory to sys.path to find permission_boundary
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from permission_boundary import Permission, PermissionBoundary, PermissionError, PrivilegeEscalationError
from event_store import SQLiteEventStore

def test_permission_creation():
    perm = Permission(
        owner_type="session",
        owner_id="session-1",
        scope=["skills"],
        capabilities=["read", "write"],
        duration_seconds=10
    )
    assert perm.owner_id == "session-1"
    assert "skills" in perm.scope
    assert "read" in perm.capabilities
    assert perm.is_expired() is False

def test_permission_expiration():
    # Set duration to negative to simulate immediate expiration
    perm = Permission(
        owner_type="agent",
        owner_id="agent-1",
        scope=["*"],
        capabilities=["read"],
        duration_seconds=-10
    )
    assert perm.is_expired() is True

def test_permission_inheritance_success(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    boundary = PermissionBoundary(event_store=store)
    
    parent = Permission(
        owner_type="session",
        owner_id="session-1",
        scope=["skills", "docs"],
        capabilities=["read", "write", "execute"]
    )
    
    child = Permission(
        owner_type="agent",
        owner_id="agent-1",
        scope=["skills/workflow-runtime"],
        capabilities=["read", "write"]
    )
    
    boundary.register_permission(parent)
    boundary.validate_inheritance(parent, child)
    # Should complete without error

def test_permission_escalation_denied():
    boundary = PermissionBoundary()
    
    parent = Permission(
        owner_type="session",
        owner_id="session-1",
        scope=["skills"],
        capabilities=["read"]
    )
    
    # 1. Child tries to escalate capabilities
    child_prio_escalation = Permission(
        owner_type="agent",
        owner_id="agent-1",
        scope=["skills"],
        capabilities=["read", "write"]  # Parents only has read
    )
    with pytest.raises(PrivilegeEscalationError):
        boundary.validate_inheritance(parent, child_prio_escalation)
        
    # 2. Child tries to escalate scope
    child_scope_escalation = Permission(
        owner_type="agent",
        owner_id="agent-1",
        scope=["docs"],  # Parents only has skills
        capabilities=["read"]
    )
    with pytest.raises(PrivilegeEscalationError):
        boundary.validate_inheritance(parent, child_scope_escalation)

def test_permission_revocation():
    boundary = PermissionBoundary()
    perm = Permission(
        owner_type="agent",
        owner_id="agent-1",
        scope=["*"],
        capabilities=["read"]
    )
    boundary.register_permission(perm)
    boundary.revoke_permission(perm.permission_id)
    assert perm.is_revoked is True
    
    child = Permission(
        owner_type="tool",
        owner_id="tool-1",
        scope=["*"],
        capabilities=["read"]
    )
    with pytest.raises(PermissionError):
        boundary.validate_inheritance(perm, child)
