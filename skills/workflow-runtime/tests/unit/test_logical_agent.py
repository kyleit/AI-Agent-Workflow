# test_logical_agent.py
import pytest
import os
import sys

# Add script directory to sys.path to find logical_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from logical_agent import LogicalAgent, AgentTransitionError
from event_store import SQLiteEventStore

def test_agent_creation():
    agent = LogicalAgent(
        agent_id="agent-1",
        session_id="session-1",
        role="Coder",
        capabilities=["coding", "debugging"],
        permissions="sandbox"
    )
    assert agent.agent_id == "agent-1"
    assert agent.role == "Coder"
    assert "coding" in agent.capabilities
    assert agent.status == "declared"
    assert agent.cancellation_state == "active"
    assert agent.retry_count == 0

def test_agent_lifecycle_transitions(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    agent = LogicalAgent(
        agent_id="agent-1",
        session_id="session-1",
        role="Coder",
        capabilities=["coding"]
    )
    
    agent.transition_to("ready", store)
    assert agent.status == "ready"
    
    agent.transition_to("scheduled", store)
    assert agent.status == "scheduled"
    
    agent.transition_to("executing", store)
    assert agent.status == "executing"
    
    agent.transition_to("completed", store)
    assert agent.status == "completed"

def test_agent_invalid_transition():
    agent = LogicalAgent(
        agent_id="agent-1",
        session_id="session-1",
        role="Coder",
        capabilities=["coding"]
    )
    with pytest.raises(AgentTransitionError):
        agent.transition_to("executing")  # Declared can't jump directly to executing

def test_agent_cancellation(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    agent = LogicalAgent(
        agent_id="agent-1",
        session_id="session-1",
        role="Coder",
        capabilities=["coding"]
    )
    
    agent.cancel(reason="test cancellation", event_store=store)
    assert agent.cancellation_state == "cancelled"
    assert agent.status == "cancelled"
    
    # Test idempotency
    agent.cancel(reason="test cancellation", event_store=store)
    assert agent.cancellation_state == "cancelled"

def test_agent_retry_policy(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    agent = LogicalAgent(
        agent_id="agent-1",
        session_id="session-1",
        role="Coder",
        capabilities=["coding"],
        retry_policy={"max_retries": 2}
    )
    
    agent.transition_to("ready", store)
    agent.transition_to("scheduled", store)
    agent.transition_to("executing", store)
    
    # Trigger retry 1
    success = agent.trigger_retry("test crash 1", store)
    assert success is True
    assert agent.retry_count == 1
    assert agent.status == "ready"
    
    agent.transition_to("scheduled", store)
    agent.transition_to("executing", store)
    
    # Trigger retry 2
    success = agent.trigger_retry("test crash 2", store)
    assert success is True
    assert agent.retry_count == 2
    
    agent.transition_to("scheduled", store)
    agent.transition_to("executing", store)
    
    # Trigger retry 3 (exceed max)
    success = agent.trigger_retry("test crash 3", store)
    assert success is False
    assert agent.status == "failed"
