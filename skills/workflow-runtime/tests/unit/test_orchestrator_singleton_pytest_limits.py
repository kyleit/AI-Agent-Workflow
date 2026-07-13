import os
import json
import pytest
import sys
import time
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from session import OSFileLock, load_config_section, DEFAULT_SPAWN_LIMITS, DEFAULT_RESOURCE_LIMITS
from hierarchical_runtime import HierarchicalRuntime

def test_singleton_lock_acquisition(tmp_path):
    lock_path = tmp_path / "orchestrator.lock"
    lock1 = OSFileLock(str(lock_path))
    lock2 = OSFileLock(str(lock_path))
    
    assert lock1.acquire() is True
    assert lock2.acquire() is False
    
    lock1.release()
    assert lock2.acquire() is True
    lock2.release()

def test_can_spawn_subagent_resource_limits(tmp_path):
    # Set up runtime mock state
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    runtime = HierarchicalRuntime("FEAT-111", state_dir=str(state_dir))
    runtime.agents = {
        "sub-1": {"role": "subagent", "status": "idle"},
        "sub-2": {"role": "subagent", "status": "idle"}
    }
    
    # Mock psutil resource usage to exceed limits and mock policy
    mock_policy = {
        "resource_limits": {
            "cpu_throttle_percent": 80,
            "memory_throttle_percent": 80
        },
        "scheduler": {
            "pause_on_high_cpu": True,
            "pause_on_high_memory": True
        }
    }
    with patch("psutil.cpu_percent", return_value=90.0), \
         patch("psutil.virtual_memory") as mock_mem, \
         patch("session.load_runtime_policy", return_value=mock_policy):
        mock_mem.return_value.percent = 50.0
        
        allowed, reason = runtime.can_spawn_subagent("sub-1", "TASK-1")
        assert allowed is False
        assert "CPU too high" in reason

def test_can_spawn_subagent_rate_limits(tmp_path):
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    runtime = HierarchicalRuntime("FEAT-111", state_dir=str(state_dir))
    runtime.agents = {
        "sub-1": {"role": "subagent", "status": "idle"}
    }
    
    with patch("psutil.cpu_percent", return_value=10.0), \
         patch("psutil.virtual_memory") as mock_mem:
        mock_mem.return_value.percent = 20.0
        
        # Trigger spawn multiple times to exceed rate limit (max 10 per minute)
        runtime.spawn_timestamps = [time.time() - 10] * 10
        
        allowed, reason = runtime.can_spawn_subagent("sub-1", "TASK-1")
        assert allowed is False
        assert "Spawn rate limit exceeded" in reason

def test_pytest_coordinator_coalescing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state_dir = tmp_path / ".agents" / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    from workflow_runtime import do_test_action
    
    # We can construct mock Args for do_test_action
    class ArgsMock:
        def __init__(self):
            self.subaction = "affected"
            
    mock_policy = {
        "resource_limits": {
            "max_pytest_workers": 2,
            "max_parallel_pytest_processes": 1
        },
        "pytest": {
            "default_mode": "affected",
            "run_full_suite_only_at_final_review": True,
            "deduplicate_requests": True
        }
    }
    
    def custom_check_output(cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 0 and cmd[0] == "git":
            if "status" in cmd:
                return b" M skills/workflow-runtime/scripts/session.py\n"
            else:
                return b"skills/workflow-runtime/scripts/session.py\n"
        return b""

    mock_p = MagicMock()
    mock_p.returncode = 0
    mock_p.stdout = ["14 passed, 0 failed in 0.5s\n"]
    mock_p.stderr = []
    mock_p.wait.return_value = 0

    # Mock subprocess.run to verify we run pytest with -n 2
    with patch("session.load_runtime_policy", return_value=mock_policy), \
         patch("subprocess.check_output", side_effect=custom_check_output), \
         patch("subprocess.Popen", return_value=mock_p) as mock_popen, \
         patch.dict("sys.modules", {"xdist": MagicMock()}), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Mocked pytest passed", stderr="")
        
        try:
            do_test_action(ArgsMock())
        except SystemExit as e:
            assert e.code == 0
            
        # Verify that cmd args executed by subprocess.Popen includes -n and 2
        pytest_call = None
        for call in mock_popen.call_args_list:
            args_list = call[0][0]
            if isinstance(args_list, list) and "pytest" in args_list:
                pytest_call = args_list
                break
                
        assert pytest_call is not None, "pytest command was not executed via subprocess.Popen"
        assert "-n" in pytest_call
        assert "2" in pytest_call
