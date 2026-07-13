# test_execution_manager_regression.py
import os
import sys
import json
import time
import pytest
import subprocess
from datetime import datetime

# Add scripts directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

from test_enforcer import patch_subprocess, is_caller_authorized
from execution_manager import ExecutionManager, ProcessRegistry

patch_subprocess()

@pytest.fixture
def mock_base_env(tmp_path, monkeypatch):
    # Setup state path redirection
    state_dir = tmp_path / ".agents" / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Redefine REGISTRY_PATH in registry for isolations
    reg_path = state_dir / "executions.json"
    monkeypatch.setattr("execution_manager.REGISTRY_PATH", str(reg_path))
    monkeypatch.setattr("execution_manager.LOGS_DIR", str(tmp_path / "logs"))
    os.makedirs(str(tmp_path / "logs"), exist_ok=True)
    
    # Mock tasks.json & agents.json
    tasks_path = state_dir / "tasks.json"
    agents_path = state_dir / "agents.json"
    
    tasks_data = {
        "tasks": {
            "TASK-001": {
                "name": "General Implementation Task",
                "role": "implementation",
                "status": "running",
                "assigned_agent": "AGENT-BACKEND-001"
            },
            "TASK-TEST": {
                "name": "QA Verification Task",
                "role": "testing",
                "status": "running",
                "assigned_agent": "AGENT-TESTER-001"
            }
        }
    }
    
    agents_data = {
        "AGENT-BACKEND-001": {"role": "developer", "type": "backend"},
        "AGENT-TESTER-001": {"role": "tester", "type": "qa"}
    }
    
    with open(tasks_path, "w", encoding="utf-8") as f:
        json.dump(tasks_data, f)
    with open(agents_path, "w", encoding="utf-8") as f:
        json.dump(agents_data, f)
        
    monkeypatch.setenv("AIWF_BASE_DIR", str(tmp_path))
    yield tmp_path

def test_strict_enforcement_prohibits_direct_run(mock_base_env, monkeypatch):
    monkeypatch.setenv("AIWF_STRICT_PROCESS_ENFORCEMENT", "true")
    
    # Direct subprocess.run should fail with PermissionError
    with pytest.raises(PermissionError) as exc:
        subprocess.run(["echo", "hello"])
    assert "Direct OS Process creation blocked" in str(exc.value)

def test_strict_enforcement_prohibits_direct_popen(mock_base_env, monkeypatch):
    monkeypatch.setenv("AIWF_STRICT_PROCESS_ENFORCEMENT", "true")
    
    # Direct subprocess.Popen should fail
    with pytest.raises(PermissionError) as exc:
        subprocess.Popen(["echo", "hello"])
    assert "Direct OS Process creation blocked" in str(exc.value)

def test_execution_manager_submits_and_runs_successfully(mock_base_env):
    req = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "python",
        "arguments": ["-c", "print('Hello Managed Process')"],
        "working_directory": str(mock_base_env),
        "timeout": 10
    }
    exec_id = ExecutionManager.submit(req)
    assert exec_id.startswith("EXEC-")
    
    # Verify created status in registry
    item = ProcessRegistry.read().get(exec_id)
    assert item["status"] == "QUEUED"
    
    # Tick scheduler to run
    ExecutionManager.tick_scheduler()
    
    # Wait until finished
    time.sleep(2.0)
    
    item = ProcessRegistry.read().get(exec_id)
    assert item["status"] in ["COMPLETED", "FAILED"]
    if item["status"] == "COMPLETED":
        assert item["exit_code"] == 0
        with open(item["stdout_artifact"], "r", encoding="utf-8") as f:
            assert "Hello Managed Process" in f.read()

def test_execution_manager_enforces_tester_role_for_tests(mock_base_env):
    # Reject: Test command submitted by non-TESTER agent
    req = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "pytest",
        "arguments": ["tests/unit"],
        "working_directory": str(mock_base_env)
    }
    with pytest.raises(PermissionError) as exc:
        ExecutionManager.submit(req)
    assert "must be owned by a TESTER or QA Agent" in str(exc.value)

    # Approve: Test command submitted by TESTER agent
    req_ok = {
        "task_id": "TASK-TEST",
        "owner_agent_id": "AGENT-TESTER-001",
        "command": "pytest",
        "arguments": ["tests/unit"],
        "working_directory": str(mock_base_env)
    }
    exec_id = ExecutionManager.submit(req_ok)
    assert exec_id.startswith("EXEC-")

def test_cancellation_terminates_process_tree(mock_base_env):
    # Run a long sleeping process
    req = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "python",
        "arguments": ["-c", "import time; time.sleep(10)"],
        "working_directory": str(mock_base_env),
        "timeout": 15
    }
    exec_id = ExecutionManager.submit(req)
    ExecutionManager.tick_scheduler()
    time.sleep(1.0)
    
    # Verify is running
    item = ProcessRegistry.read().get(exec_id)
    assert item["status"] == "RUNNING"
    pid = item["pid"]
    assert pid is not None
    
    # Cancel it
    ExecutionManager.cancel(exec_id, reason="User Cancelled Test")
    time.sleep(1.5)
    
    # Verify stopped
    item = ProcessRegistry.read().get(exec_id)
    assert item["status"] == "CANCELLED"
    assert not ExecutionManager.is_pid_alive(pid)

def test_timeout_policy_terminates_process(mock_base_env):
    # Run process with small timeout
    req = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "python",
        "arguments": ["-c", "import time; time.sleep(10)"],
        "working_directory": str(mock_base_env),
        "timeout": 2 # 2 seconds timeout
    }
    exec_id = ExecutionManager.submit(req)
    ExecutionManager.tick_scheduler()
    
    # Wait for timeout to fire
    time.sleep(4.0)
    
    item = ProcessRegistry.read().get(exec_id)
    assert item["status"] == "TIMED_OUT"
    assert "timed out after" in item["termination_reason"]

def test_interactive_blocked_commands_detected(mock_base_env):
    # Run script printing interactive keywords under stdin_mode: disabled
    req = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "python",
        "arguments": ["-c", "import time, sys; print('confirm [y/n]:'); sys.stdout.flush(); time.sleep(5)"],
        "working_directory": str(mock_base_env),
        "timeout": 10,
        "stdin_mode": "disabled"
    }
    exec_id = ExecutionManager.submit(req)
    ExecutionManager.tick_scheduler()
    
    time.sleep(2.0)
    
    item = ProcessRegistry.read().get(exec_id)
    assert item["status"] == "BLOCKED_INTERACTIVE"
    assert "blocked waiting for stdin prompt" in item["termination_reason"]

def test_capacity_limitation_queues_process(mock_base_env, monkeypatch):
    # Force mock get_system_capacity to return 1 CPU
    monkeypatch.setattr("execution_manager.ExecutionManager.get_system_capacity", lambda: (1, 8*1024**3, 4*1024**3))
    
    # Submit first process using 1.0 CPU
    req1 = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "python",
        "arguments": ["-c", "import time; time.sleep(4)"],
        "working_directory": str(mock_base_env),
        "cpu_limit": 1.0
    }
    # Submit second process using 1.0 CPU
    req2 = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "python",
        "arguments": ["-c", "import time; time.sleep(4)"],
        "working_directory": str(mock_base_env),
        "cpu_limit": 1.0
    }
    
    exec_id1 = ExecutionManager.submit(req1)
    exec_id2 = ExecutionManager.submit(req2)
    
    # Tick scheduler
    ExecutionManager.tick_scheduler()
    time.sleep(0.5)
    
    item1 = ProcessRegistry.read().get(exec_id1)
    item2 = ProcessRegistry.read().get(exec_id2)
    
    # First should start, second should stay QUEUED
    assert item1["status"] == "RUNNING"
    assert item2["status"] == "QUEUED"
    
    # Cleanup
    ExecutionManager.kill(exec_id1)
    ExecutionManager.kill(exec_id2)

def test_orphan_detection_and_recovery(mock_base_env):
    # Submit and run a long sleeping process
    req = {
        "task_id": "TASK-001",
        "owner_agent_id": "AGENT-BACKEND-001",
        "command": "python",
        "arguments": ["-c", "import time; time.sleep(10)"],
        "working_directory": str(mock_base_env),
        "timeout": 15
    }
    exec_id = ExecutionManager.submit(req)
    ExecutionManager.tick_scheduler()
    time.sleep(1.0)
    
    item = ProcessRegistry.read().get(exec_id)
    pid = item["pid"]
    
    # We clear standard python runtime state (simulating a crash / restart)
    # Recover should find active process and re-attach
    recovered = ExecutionManager.recover()
    assert exec_id in recovered
    
    # Cleanup
    ExecutionManager.kill(exec_id)

def test_run_command_managed_helper(mock_base_env):
    # Test transparent redirect (managed run compatibility helper)
    res = ExecutionManager.run_command_managed(
        ["python", "-c", "print('Redirect Hello')"],
        cwd=str(mock_base_env)
    )
    assert res.returncode == 0
    assert "Redirect Hello" in res.stdout
