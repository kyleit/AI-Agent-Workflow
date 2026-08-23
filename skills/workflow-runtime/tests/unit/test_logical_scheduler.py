# test_logical_scheduler.py
import pytest
import asyncio
import os
import sys

# Add script directory to sys.path to find logical_scheduler
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from logical_scheduler import Task, Worker, BoundedWorkerPool, LogicalScheduler, TaskTransitionError
from event_store import SQLiteEventStore

def test_task_creation():
    task = Task(
        task_id="task-1",
        session_id="session-1",
        agent_id="agent-1",
        priority="high",
        dependencies=["task-0"]
    )
    assert task.task_id == "task-1"
    assert task.status == "created"
    assert "task-0" in task.dependencies

def test_task_invalid_transition():
    task = Task(task_id="task-1", session_id="session-1", agent_id="agent-1")
    with pytest.raises(TaskTransitionError):
        task.transition_to("running")  # Can't go directly from created to running without queued/scheduled

@pytest.mark.asyncio
async def test_worker_pool_lifecycle(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    pool = BoundedWorkerPool(session_id="session-1", max_workers=2, event_store=store)
    
    assert len(pool.workers) == 2
    worker = await pool.get_idle_worker()
    assert worker is not None
    assert worker.status == "idle"
    
    # Assign worker 1
    await pool.assign_worker(worker_id=worker.worker_id, task_id="task-1")
    assert worker.status == "assigned"
    assert worker.assigned_task_id == "task-1"
    
    # Get worker 2
    worker2 = await pool.get_idle_worker()
    assert worker2 is not None
    assert worker2.worker_id != worker.worker_id
    assert worker2.status == "idle"
    
    # Assign worker 2
    await pool.assign_worker(worker_id=worker2.worker_id, task_id="task-2")
    assert worker2.status == "assigned"
    
    # Now pool has no more idle workers, should return None
    worker3 = await pool.get_idle_worker()
    assert worker3 is None
    
    # Release worker 1
    await pool.release_worker(worker_id=worker.worker_id)
    assert worker.status == "idle"
    
    # Idle worker should be available again
    worker_avail = await pool.get_idle_worker()
    assert worker_avail.worker_id == worker.worker_id

@pytest.mark.asyncio
async def test_scheduler_priority_and_dag(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    pool = BoundedWorkerPool(session_id="session-1", max_workers=2, event_store=store)
    scheduler = LogicalScheduler(session_id="session-1", worker_pool=pool, event_store=store)
    
    # Define tasks
    t0 = Task(task_id="t0", session_id="session-1", agent_id="agent-1", priority="low")
    t1 = Task(task_id="t1", session_id="session-1", agent_id="agent-1", priority="high", dependencies=["t0"])
    t2 = Task(task_id="t2", session_id="session-1", agent_id="agent-1", priority="medium")
    
    await scheduler.submit_task(t0)
    await scheduler.submit_task(t1)
    await scheduler.submit_task(t2)
    
    # Dispatch check 1: t1 depends on t0, so only t0 (low) and t2 (medium) are satisfying dependencies
    # Out of t0 and t2, t2 has higher priority ("medium" > "low"), so it should be dispatched first.
    dispatch1 = await scheduler.dispatch_next()
    assert dispatch1 is not None
    task_dispatched, worker_assigned = dispatch1
    assert task_dispatched.task_id == "t2"
    
    # Dispatch check 2: t0 should be next since t1 is blocked by t0
    dispatch2 = await scheduler.dispatch_next()
    assert dispatch2 is not None
    assert dispatch2[0].task_id == "t0"

@pytest.mark.asyncio
async def test_scheduler_backpressure(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    pool = BoundedWorkerPool(session_id="session-1", max_workers=2, event_store=store)
    scheduler = LogicalScheduler(session_id="session-1", worker_pool=pool, queue_limit=1, event_store=store)
    
    t0 = Task(task_id="t0", session_id="session-1", agent_id="agent-1")
    t1 = Task(task_id="t1", session_id="session-1", agent_id="agent-2")
    
    await scheduler.submit_task(t0)
    # Queue is full, should trigger ResourceWarning backpressure
    with pytest.raises(ResourceWarning):
        await scheduler.submit_task(t1)
        
@pytest.mark.asyncio
async def test_scheduler_cpu_throttling(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    pool = BoundedWorkerPool(session_id="session-1", max_workers=2, event_store=store)
    scheduler = LogicalScheduler(session_id="session-1", worker_pool=pool, event_store=store)
    
    t0 = Task(task_id="t0", session_id="session-1", agent_id="agent-1")
    await scheduler.submit_task(t0)
    
    # Simulate high CPU pressure
    scheduler.mock_cpu_usage = 95.0
    dispatch = await scheduler.dispatch_next()
    assert dispatch is None  # Throttled
    
    events = store.get_events("session-1")
    topics = [e["topic"] for e in events]
    assert "scheduler.throttled" in topics
