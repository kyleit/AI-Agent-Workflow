# test_external_executor.py
import pytest
import os
import sys
import asyncio
import subprocess

# Add script directory to sys.path to find external_executor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from external_executor import ToolRequest, ToolResult, ToolExecutor, ForbiddenProcessSpawnError
from event_store import SQLiteEventStore

def test_tool_request_and_result():
    req = ToolRequest(
        session_id="session-1",
        agent_id="agent-1",
        task_id="task-1",
        command="pytest",
        arguments=["-v"]
    )
    assert req.command == "pytest"
    assert req.arguments == ["-v"]
    
    res = ToolResult(exit_code=0, stdout="passed", stderr="", duration=1.2)
    assert res.exit_code == 0
    assert res.error_category == "none"

def test_permission_boundary_validation():
    executor = ToolExecutor()
    
    # 1. Invalid command registry check
    req = ToolRequest(
        session_id="session-1",
        agent_id="agent-1",
        task_id="task-1",
        command="rm",  # Forbidden command
        arguments=["-rf", "/"]
    )
    with pytest.raises(PermissionError):
        executor.validate_request(req)
        
    # 2. Sandbox directory path check
    req_sandbox_violation = ToolRequest(
        session_id="session-1",
        agent_id="agent-1",
        task_id="task-1",
        command="git",
        cwd="/etc"  # Outside workspace root
    )
    with pytest.raises(PermissionError):
        executor.validate_request(req_sandbox_violation)

def test_retry_classification():
    executor = ToolExecutor()
    assert executor.classify_error(exit_code=124, stderr="") == "timeout"
    assert executor.classify_error(exit_code=1, stderr="permission denied") == "permission_denied"
    assert executor.classify_error(exit_code=127, stderr="command not found") == "invalid_command"
    assert executor.classify_error(exit_code=1, stderr="syntax error") == "compile_error"
    assert executor.classify_error(exit_code=2, stderr="unknown failed test") == "retryable_failure"

@pytest.mark.asyncio
async def test_tool_execution_success(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    executor = ToolExecutor(event_store=store)
    
    req = ToolRequest(
        session_id="session-1",
        agent_id="agent-1",
        task_id="task-1",
        command="python3",
        arguments=["-c", "print('hello world')"]
    )
    
    res = await executor.execute_tool(req)
    assert res.exit_code == 0
    assert "hello world" in res.stdout
    
    events = store.get_events("session-1")
    topics = [e["topic"] for e in events]
    assert "tool.requested" in topics
    assert "tool.completed" in topics

@pytest.mark.asyncio
async def test_tool_execution_timeout(tmp_path):
    store = SQLiteEventStore(workspace_root=str(tmp_path))
    executor = ToolExecutor(event_store=store)
    
    req = ToolRequest(
        session_id="session-1",
        agent_id="agent-1",
        task_id="task-1",
        command="python3",
        arguments=["-c", "import time; time.sleep(10)"],
        timeout=0.1  # Fast timeout
    )
    
    res = await executor.execute_tool(req)
    assert res.exit_code == 124
    assert res.error_category == "timeout"
    
    events = store.get_events("session-1")
    topics = [e["topic"] for e in events]
    assert "tool.timeout" in topics

def test_global_runtime_validator_intercept():
    # Triggering direct subprocess spawn call without using ToolExecutor wrapper
    # should raise ForbiddenProcessSpawnError
    with pytest.raises(ForbiddenProcessSpawnError):
        subprocess.run(["python3", "-c", "print('bypass')"])
        
    with pytest.raises(ForbiddenProcessSpawnError):
        subprocess.Popen(["python3", "-c", "print('bypass Popen')"])
