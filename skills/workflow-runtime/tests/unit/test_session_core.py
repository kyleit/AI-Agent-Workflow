# test_session_core.py
import pytest
import os
import sys
import json

# Add script directory to sys.path to find session_core and event_store
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session_core import SessionRuntimeCore, create_session, SessionInitError, checkpoint_session, recover_session, SessionNotFoundError
from event_store import SQLiteEventStore

def test_session_runtime_init():
    session = SessionRuntimeCore(session_id="test-session", permission_mode="sandbox")
    assert session.session_id == "test-session"
    assert session.permission_mode == "sandbox"
    assert session.status == "created"

def test_session_valid_transitions():
    session = SessionRuntimeCore(session_id="test-session")
    session.transition_to("initializing")
    assert session.status == "initializing"
    
    session.transition_to("planning")
    assert session.status == "planning"
    
    session.transition_to("ready")
    assert session.status == "ready"
    
    session.transition_to("running")
    assert session.status == "running"
    
    session.transition_to("waiting_for_tool")
    assert session.status == "waiting_for_tool"
    
    session.transition_to("running")
    assert session.status == "running"
    
    session.transition_to("integrating")
    assert session.status == "integrating"
    
    session.transition_to("verifying")
    assert session.status == "verifying"
    
    session.transition_to("completed")
    assert session.status == "completed"

def test_session_invalid_transition():
    session = SessionRuntimeCore(session_id="test-session")
    with pytest.raises(ValueError):
        session.transition_to("verifying")  # Can't jump from created directly to verifying

def test_create_session_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    session = create_session(request_id="req-1", work_item="FEAT-211")
    assert session.active_work_item_id == "FEAT-211"
    assert session.status == "initializing"

def test_create_session_failure_missing_agents_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SessionInitError):
        create_session(request_id="req-1", work_item="FEAT-211")

def test_checkpoint_and_recover(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # Init store & session
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="req-1", work_item="FEAT-211", permission_mode="full_access")
    session.transition_to("planning")
    session.transition_to("ready")
    
    # Perform checkpoint
    checkpoint_session(session, store)
    
    # Check context.json was written correctly
    context_path = os.path.join(".agents", "state", "context.json")
    assert os.path.exists(context_path)
    with open(context_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["session_id"] == session.session_id
    assert data["permission_mode"] == "full_access"
    assert data["checkpoint_status"] == "ready"
    
    # Recover session
    recovered = recover_session(session.session_id, store)
    assert recovered.session_id == session.session_id
    assert recovered.permission_mode == "full_access"
    assert recovered.status == "ready"
    assert recovered.active_work_item_id == "FEAT-211"

def test_recover_nonexistent_session(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    with pytest.raises(SessionNotFoundError):
        recover_session("non-existent-uuid", store)
