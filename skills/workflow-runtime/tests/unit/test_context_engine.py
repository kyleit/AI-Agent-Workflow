# test_context_engine.py
import pytest
import asyncio
import os
import sys

# Add script directory to sys.path to find context_engine
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from context_engine import SharedContextEngine, StateConflictError, SharedSessionContext, AgentContextDelta
from event_store import SQLiteEventStore

def test_shared_session_context_creation():
    ctx = SharedSessionContext(
        context_id="ctx-1",
        session_id="session-1",
        version=1,
        content_refs={"token": 10},
        metadata={"user": "admin"}
    )
    assert ctx.context_id == "ctx-1"
    assert ctx.version == 1
    assert ctx.content_refs["token"] == 10
    assert ctx.hash is not None

def test_agent_delta_creation():
    delta = AgentContextDelta(agent_id="agent-1")
    delta.local_changes = {"changed_file": "main.py"}
    delta.local_decisions.append("fix bug")
    delta.scratch_data = {"temp": 12}
    delta.evidence_references.append("test case fail")
    delta.output_summaries = "fixed compilation"
    
    d = delta.to_dict()
    assert d["agent_id"] == "agent-1"
    assert d["local_changes"]["changed_file"] == "main.py"
    assert d["local_decisions"][0] == "fix bug"

@pytest.mark.asyncio
async def test_context_init_and_slice(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    initial = {"project_name": "AIWF", "languages": ["Python", "Go"], "token_count": 100}
    engine = SharedContextEngine(session_id="session-1", initial_content=initial, event_store=store)
    
    # Test slice read
    ctx_slice = await engine.get_context_slice(["project_name", "languages"])
    assert ctx_slice["revision"] == 1
    assert ctx_slice["data"]["project_name"] == "AIWF"
    assert "Python" in ctx_slice["data"]["languages"]
    assert "token_count" not in ctx_slice["data"]
    
    # Verify event context.created is logged
    events = store.get_events("session-1")
    assert len(events) == 1
    assert events[0]["topic"] == "context.created"

@pytest.mark.asyncio
async def test_occ_merge_success(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    initial = {"token_count": 100}
    engine = SharedContextEngine(session_id="session-1", initial_content=initial, event_store=store)
    
    ctx_slice = await engine.get_context_slice(["token_count"])
    base_rev = ctx_slice["revision"]
    
    # Delta update
    new_rev = await engine.merge_delta(
        base_revision=base_rev,
        delta={"token_count": 150, "new_field": "val"},
        agent_id="agent-coder",
        expected_hash=ctx_slice["hash"]
    )
    assert new_rev == 2
    assert engine.revision == 2
    
    full_ctx = await engine.get_full_context()
    assert full_ctx["token_count"] == 150
    assert full_ctx["new_field"] == "val"
    
    # Check if correct snapshots are stored
    assert len(engine._snapshots) == 2
    
    # Verify events
    events = store.get_events("session-1")
    topics = [e["topic"] for e in events]
    assert "context.merge_requested" in topics
    assert "context.snapshot_created" in topics
    assert "context.version_updated" in topics

@pytest.mark.asyncio
async def test_occ_merge_conflict(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    initial = {"token_count": 100}
    engine = SharedContextEngine(session_id="session-1", initial_content=initial, event_store=store)
    
    slice_a = await engine.get_context_slice(["token_count"])
    slice_b = await engine.get_context_slice(["token_count"])
    
    # Client A merges successfully
    await engine.merge_delta(base_revision=slice_a["revision"], delta={"token_count": 120})
    assert engine.revision == 2
    
    # Client B merges with STALE revision -> Should raise conflict
    with pytest.raises(StateConflictError):
        await engine.merge_delta(base_revision=slice_b["revision"], delta={"token_count": 130})
        
    events = store.get_events("session-1")
    topics = [e["topic"] for e in events]
    assert "context.merge_rejected" in topics

@pytest.mark.asyncio
async def test_concurrency_race_condition():
    engine = SharedContextEngine(session_id="session-1", initial_content={"count": 0})
    
    async def worker(index: int):
        # Read slice
        ctx_slice = await engine.get_context_slice(["count"])
        val = ctx_slice["data"]["count"]
        
        # Sleep to let all workers read the same base_revision before any worker merges
        await asyncio.sleep(0.01)
        
        # Add delta
        try:
            await engine.merge_delta(base_revision=ctx_slice["revision"], delta={"count": val + 1})
            return True
        except StateConflictError:
            return False  # Failed due to conflict
            
    # Run 10 workers in parallel
    results = await asyncio.gather(*(worker(i) for i in range(10)))
    success_count = sum(1 for r in results if r)
    
    # Because they all read base_revision=1 at nearly the same time,
    # ONLY ONE worker should successfully commit, others must fail with conflict.
    assert success_count == 1
    assert engine.revision == 2
    full_ctx = await engine.get_full_context()
    assert full_ctx["count"] == 1
