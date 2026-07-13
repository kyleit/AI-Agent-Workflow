# test_executor_integration.py
import pytest
import os
import sys
import asyncio

# Add script directory to sys.path to find core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session_core import SessionRuntimeCore, create_session
from event_store import SQLiteEventStore
from logical_agent import LogicalAgent
from logical_scheduler import Task, BoundedWorkerPool, LogicalScheduler
from external_executor import ToolRequest, ToolExecutor

@pytest.mark.asyncio
async def test_scheduler_agent_executor_integration(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # 1. Init Session & Event Store
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="req-999", work_item="FEAT-211")
    
    # 2. Init Scheduler & Worker Pool
    pool = BoundedWorkerPool(session_id=session.session_id, max_workers=2, event_store=store)
    scheduler = LogicalScheduler(session_id=session.session_id, worker_pool=pool, event_store=store)
    
    # 3. Init Agent & Executor
    agent = LogicalAgent(
        agent_id="agent-coder",
        session_id=session.session_id,
        role="Coder",
        capabilities=["coding"]
    )
    executor = ToolExecutor(event_store=store)
    
    # 4. Submit Task
    t0 = Task(task_id="t0", session_id=session.session_id, agent_id=agent.agent_id)
    await scheduler.submit_task(t0)
    
    # Dispatch
    dispatch = await scheduler.dispatch_next()
    assert dispatch is not None
    task, worker = dispatch
    
    # Execute Task using Tool Executor Subsystem wrapper (Authorized spawn)
    task.transition_to("running", store)
    
    req = ToolRequest(
        session_id=session.session_id,
        agent_id=agent.agent_id,
        task_id=task.task_id,
        command="python3",
        arguments=["-c", "print('integration success')"]
    )
    
    # Call through ToolExecutor gateway
    res = await executor.execute_tool(req)
    assert res.exit_code == 0
    assert "integration success" in res.stdout
    
    # Complete task
    task.transition_to("completed", store)
    await pool.release_worker(worker.worker_id)
    
    assert t0.status == "completed"
    
    # 5. Check events timeline in event store
    events = store.get_events(session.session_id)
    topics = [e["topic"] for e in events]
    assert "tool.requested" in topics
    assert "tool.completed" in topics
