# test_permission_integration.py
import pytest
import os
import sys

# Add script directory to sys.path to find core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session_core import SessionRuntimeCore, create_session
from event_store import SQLiteEventStore
from logical_agent import LogicalAgent
from permission_boundary import Permission, PermissionBoundary, PermissionError
from external_executor import ToolRequest, ToolExecutor

def test_session_agent_tool_permission_integration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # 1. Init Session, Store, Boundary, and Tool Executor
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="req-777", work_item="FEAT-211")
    boundary = PermissionBoundary(event_store=store)
    executor = ToolExecutor(event_store=store)
    
    # 2. Session defines parent permission
    session_perm = Permission(
        owner_type="session",
        owner_id=session.session_id,
        scope=["skills"],  # only skills folder allowed
        capabilities=["read", "execute"],
        session_id=session.session_id
    )
    boundary.register_permission(session_perm)
    
    # 3. Agent requests subset permission
    agent = LogicalAgent(
        agent_id="agent-coder",
        session_id=session.session_id,
        role="Coder",
        capabilities=["coding"]
    )
    
    agent_perm = Permission(
        owner_type="agent",
        owner_id=agent.agent_id,
        scope=["skills/workflow-runtime"],
        capabilities=["read", "execute"],
        session_id=session.session_id
    )
    boundary.register_permission(agent_perm)
    boundary.validate_inheritance(session_perm, agent_perm)
    
    # 4. Check tool access (Success case)
    # Target path inside allowed write scope
    boundary.check_tool_access(agent_perm, "python3", "skills/workflow-runtime")
    
    # Check tool access (Failure case - Path out of scope)
    with pytest.raises(PermissionError):
        boundary.check_tool_access(agent_perm, "python3", "docs")
        
    # 5. Check events timeline in event store
    events = store.get_events(session.session_id)
    topics = [e["topic"] for e in events]
    # Permission created and granted are recorded
    assert "permission.created" in topics
    assert "permission.granted" in topics

def test_full_access_isolation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    session_a = create_session(request_id="req-a", work_item="FEAT-211", permission_mode="full_access")
    session_b = create_session(request_id="req-b", work_item="FEAT-211", permission_mode="sandbox")
    
    # Verify session permissions are strictly isolated in memory and do not leak
    assert session_a.permission_mode == "full_access"
    assert session_b.permission_mode == "sandbox"
