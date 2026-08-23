# test_scheduler_integration.py
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

@pytest.mark.asyncio
async def test_session_scheduler_agent_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # 1. Init Session & Event Store
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="req-555", work_item="FEAT-211")
    
    # 2. Init Bounded Worker Pool & Scheduler
    pool = BoundedWorkerPool(session_id=session.session_id, max_workers=2, event_store=store)
    scheduler = LogicalScheduler(session_id=session.session_id, worker_pool=pool, event_store=store)
    
    # 3. Init Logical Agent
    agent = LogicalAgent(
        agent_id="agent-planner",
        session_id=session.session_id,
        role="Planner",
        capabilities=["planning"]
    )
    
    # 4. Submit Task DAG: t0 -> t1 (t1 depends on t0)
    t0 = Task(task_id="t0", session_id=session.session_id, agent_id=agent.agent_id)
    t1 = Task(task_id="t1", session_id=session.session_id, agent_id=agent.agent_id, dependencies=["t0"])
    
    await scheduler.submit_task(t0)
    await scheduler.submit_task(t1)
    
    # Verify tasks are queued
    assert t0.status == "queued"
    assert t1.status == "queued"
    
    # Dispatch and execute t0
    dispatch_t0 = await scheduler.dispatch_next()
    assert dispatch_t0 is not None
    task_t0, worker_t0 = dispatch_t0
    assert task_t0.task_id == "t0"
    
    # Run simulated execution
    await scheduler.execute_task_simulated(task_t0.task_id, worker_t0.worker_id)
    assert t0.status == "completed"
    
    # Dispatch and execute t1 (now satisfied)
    dispatch_t1 = await scheduler.dispatch_next()
    assert dispatch_t1 is not None
    task_t1, worker_t1 = dispatch_t1
    assert task_t1.task_id == "t1"
    
    await scheduler.execute_task_simulated(task_t1.task_id, worker_t1.worker_id)
    assert t1.status == "completed"
    
    # 5. Recovery Verification
    # Replay events to rebuild scheduler tasks state
    recovered_scheduler = LogicalScheduler(session_id=session.session_id, worker_pool=pool)
    events = store.get_events(session.session_id)
    
    for event in events:
        topic = event["topic"]
        payload = event["payload"]
        if topic == "task.queued":
            recovered_scheduler.tasks[payload["task_id"]] = Task(
                task_id=payload["task_id"],
                session_id=session.session_id,
                agent_id=agent.agent_id
            )
            recovered_scheduler.tasks[payload["task_id"]].status = "queued"
        elif topic.startswith("task."):
            status = topic.split(".")[1]
            if payload["task_id"] in recovered_scheduler.tasks:
                recovered_scheduler.tasks[payload["task_id"]].status = status
                
    assert recovered_scheduler.tasks["t0"].status == "completed"
    assert recovered_scheduler.tasks["t1"].status == "completed"
