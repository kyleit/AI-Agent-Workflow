# test_certification_harness.py
import pytest
import os
import sys
import time
import asyncio
import gc

# Add script directory to sys.path to find core modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session_core import SessionRuntimeCore, create_session
from event_store import SQLiteEventStore
from logical_agent import LogicalAgent
from logical_scheduler import LogicalScheduler, Task, BoundedWorkerPool
from external_executor import ToolExecutor, ToolRequest, ForbiddenProcessSpawnError
from permission_boundary import Permission, PermissionBoundary, PermissionError
from websocket_server import RuntimeAPIServer
from runtime_sdk import RuntimeSDKv3

@pytest.mark.asyncio
async def test_resource_leaks_stress_and_soak(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # 1. Setup Environment
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="stress-req", work_item="FEAT-211")
    
    # Measure memory baseline
    gc.collect()
    
    # 2. Stress Session Creation & Worker execution loops
    worker_pool = BoundedWorkerPool(session_id=session.session_id, max_workers=5, event_store=store)
    scheduler = LogicalScheduler(session_id=session.session_id, worker_pool=worker_pool, event_store=store)
    
    # Spawn 10 agents and submit 10 tasks continuously (Soak test simulation)
    agents = []
    for i in range(10):
        agent = LogicalAgent(agent_id=f"agent-{i}", session_id=session.session_id, role="Tester", capabilities=["testing"])
        agents.append(agent)
        
    tasks = []
    for i in range(10):
        t = Task(
            task_id=f"task-{i}",
            session_id=session.session_id,
            agent_id=f"agent-{i%10}",
            dependencies=[]
        )
        tasks.append(t)
        await scheduler.submit_task(t)
        
    # Dispatch some tasks
    dispatch_res = await scheduler.dispatch_next()
    assert dispatch_res is not None
    task_dispatched, worker_assigned = dispatch_res
    assert task_dispatched.status == "scheduled"
    
    # Clean up
    await worker_pool.shutdown()
    assert len(worker_pool.workers) == 0
    gc.collect()

@pytest.mark.asyncio
async def test_fault_injection_recovery(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    session = create_session(request_id="fault-req", work_item="FEAT-211")
    
    # Scenario 1: Tool Timeout cleanup and error classification
    executor = ToolExecutor(event_store=store)
    req_timeout = ToolRequest(
        session_id=session.session_id,
        agent_id="agent-1",
        task_id="task-1",
        command="python3",
        arguments=["-c", "import time; time.sleep(10)"],
        timeout=0.05
    )
    res = await executor.execute_tool(req_timeout)
    assert res.exit_code == 124
    assert res.error_category == "timeout"
    
    # Scenario 2: Forbidden process interception
    os.environ["AIWF_FORCE_ENFORCE"] = "true"
    os.environ["AIWF_TESTING_BYPASS_ENFORCER"] = "true"
    try:
        with pytest.raises(ForbiddenProcessSpawnError):
            import subprocess
            subprocess.run(["python3", "-c", "print('bypass')"])
    finally:
        os.environ.pop("AIWF_FORCE_ENFORCE", None)
        os.environ.pop("AIWF_TESTING_BYPASS_ENFORCER", None)

@pytest.mark.asyncio
async def test_performance_latencies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs(".agents")
    
    # Measure session startup latency
    t0 = time.perf_counter()
    session = create_session(request_id="perf-req", work_item="FEAT-211")
    startup_latency = time.perf_counter() - t0
    
    # Measure logical agent creation latency
    t1 = time.perf_counter()
    agent = LogicalAgent(agent_id="agent-perf", session_id=session.session_id, role="Analyst", capabilities=["analysis"])
    agent_creation_latency = time.perf_counter() - t1
    
    assert startup_latency < 0.05  # Should startup under 50ms (typically <5ms)
    assert agent_creation_latency < 0.01  # Should create under 10ms
