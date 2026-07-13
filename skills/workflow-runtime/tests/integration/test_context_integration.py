# test_context_integration.py
import pytest
import os
import sys
import asyncio

# Add script directory to sys.path to find context_engine, event_store, and logical_agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session_core import SessionRuntimeCore, create_session
from event_store import SQLiteEventStore
from context_engine import SharedContextEngine, StateConflictError
from logical_agent import LogicalAgent

@pytest.mark.asyncio
async def test_session_context_agent_integration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # 1. Session creates Shared Context
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="req-123", work_item="FEAT-211")
    
    initial_data = {"project": "AIWF", "owner": "Ba"}
    engine = SharedContextEngine(session_id=session.session_id, initial_content=initial_data, event_store=store)
    
    # 2. Agent reads Shared Context
    agent = LogicalAgent(
        agent_id="agent-coder",
        session_id=session.session_id,
        role="Coder",
        capabilities=["coding"]
    )
    
    ctx_slice = await engine.get_context_slice(["project", "owner"])
    assert ctx_slice["data"]["project"] == "AIWF"
    
    # 3. Agent creates Delta and requests Merge
    agent.context_delta["local_changes"] = {"changed_file": "main.py"}
    await engine.merge_delta(
        base_revision=ctx_slice["revision"],
        delta={"project": "AIWF Redesign"},
        agent_id=agent.agent_id,
        expected_hash=ctx_slice["hash"]
    )
    
    full_ctx = await engine.get_full_context()
    assert full_ctx["project"] == "AIWF Redesign"
    assert engine.revision == 2
    
    # 4. Version Conflict Detection
    # Stale read representation
    with pytest.raises(StateConflictError):
        await engine.merge_delta(
            base_revision=ctx_slice["revision"],  # Using revision 1 (stale, current is 2)
            delta={"owner": "Kyle"},
            agent_id=agent.agent_id,
            expected_hash=ctx_slice["hash"]
        )
        
    # 5. Recovery from EventStore (simulating replay after crash)
    recovered_engine = SharedContextEngine(session_id=session.session_id, initial_content=initial_data)
    
    events = store.get_events(session.session_id)
    # Replay context events
    for event in events:
        topic = event["topic"]
        payload = event["payload"]
        
        if topic == "context.snapshot_created":
            recovered_engine.revision = payload["version"]
            recovered_engine._snapshots[payload["version"]] = payload
            # Simply update the state count pointer in recovered simulation
            
    assert recovered_engine.revision == 2
