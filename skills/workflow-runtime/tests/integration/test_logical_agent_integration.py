# test_logical_agent_integration.py
import pytest
import os
import sys
import json

# Add script directory to sys.path to find session_core, event_store, and logical_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session_core import SessionRuntimeCore, create_session, checkpoint_session
from event_store import SQLiteEventStore
from logical_agent import LogicalAgent

def test_session_agent_creation_and_persistence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # 1. Session creates Logical Agent
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="req-123", work_item="FEAT-211")
    
    agent = LogicalAgent(
        agent_id="agent-coder",
        session_id=session.session_id,
        role="Coder",
        capabilities=["coding"]
    )
    
    # Save initialization event
    store.append_event(
        session_id=session.session_id,
        topic="agent.created",
        payload=agent.to_dict()
    )
    
    # 2. Transition state and check persistence in event store
    agent.transition_to("ready", store)
    agent.transition_to("scheduled", store)
    agent.transition_to("executing", store)
    
    events = store.get_events(session.session_id)
    # Events expected: session.checkpoint (from init implicit or check), agent.created, agent.ready, agent.scheduled, agent.executing
    agent_events = [e for e in events if e["topic"].startswith("agent.")]
    assert len(agent_events) == 4
    assert agent_events[0]["topic"] == "agent.created"
    assert agent_events[3]["topic"] == "agent.executing"
    
    # 3. Crash and Recovery simulation (Event Replay)
    recovered_agent = LogicalAgent(
        agent_id="agent-coder",
        session_id=session.session_id,
        role="Coder",
        capabilities=["coding"]
    )
    
    # Replay events to restore agent state
    for event in events:
        if event["topic"] == "agent.created" and event["payload"]["agent_id"] == "agent-coder":
            payload = event["payload"]
            recovered_agent.goal = payload.get("goal", "")
            recovered_agent.retry_count = payload.get("retry_count", 0)
        elif event["topic"].startswith("agent.") and event["payload"]["agent_id"] == "agent-coder":
            recovered_agent.status = event["payload"]["status"]
            
    assert recovered_agent.status == "executing"
    assert recovered_agent.role == "Coder"
