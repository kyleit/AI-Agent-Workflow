import os
import json
import pytest
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from session import (
    load_runtime_policy,
    get_runtime_policy_path,
    validate_runtime_policy,
    write_runtime_policy,
    DEFAULT_RUNTIME_POLICY
)
from workflow_runtime import do_init, do_test_action, do_runtime_action
from hierarchical_runtime import HierarchicalRuntime

class ArgsMock:
    def __init__(self, name="TestProj", path=".", non_interactive=True, config=None, dry_run=False, resume=False, permission="sandbox"):
        self.name = name
        self.path = path
        self.non_interactive = non_interactive
        self.config = config
        self.dry_run = dry_run
        self.resume = resume
        self.permission = permission
        self.action = "init"
        self.subaction = None
        self.policy_action = None

def test_auto_create_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    # Configure root env var so path is local to tmp_path
    monkeypatch.setenv("AIWF_RUNTIME_POLICY_ROOT", str(tmp_path))
    
    policy_path = get_runtime_policy_path()
    assert not os.path.exists(policy_path)
    
    policy = load_runtime_policy(validate=True)
    assert os.path.exists(policy_path)
    assert policy["resource_limits"]["max_subagents"] == 4
    assert policy["scheduler"]["adaptive_concurrency"] is True

def test_existing_reused(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIWF_RUNTIME_POLICY_ROOT", str(tmp_path))
    
    policy_path = get_runtime_policy_path()
    os.makedirs(os.path.dirname(policy_path), exist_ok=True)
    
    custom_policy = DEFAULT_RUNTIME_POLICY.copy()
    custom_policy["resource_limits"] = custom_policy["resource_limits"].copy()
    custom_policy["resource_limits"]["max_subagents"] = 99
    
    with open(policy_path, "w", encoding="utf-8") as f:
        json.dump(custom_policy, f)
        
    policy = load_runtime_policy(validate=True)
    assert policy["resource_limits"]["max_subagents"] == 99

def test_invalid_schema_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIWF_RUNTIME_POLICY_ROOT", str(tmp_path))
    
    policy_path = get_runtime_policy_path()
    os.makedirs(os.path.dirname(policy_path), exist_ok=True)
    
    # invalid type for max_subagents (string instead of int)
    invalid_policy = DEFAULT_RUNTIME_POLICY.copy()
    invalid_policy["resource_limits"] = invalid_policy["resource_limits"].copy()
    invalid_policy["resource_limits"]["max_subagents"] = "four"
    
    with open(policy_path, "w", encoding="utf-8") as f:
        json.dump(invalid_policy, f)
        
    with pytest.raises(ValueError) as exc:
        load_runtime_policy(validate=True)
    assert "Invalid runtime-policy.json schema" in str(exc.value)

def test_init_idempotent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIWF_RUNTIME_POLICY_ROOT", str(tmp_path))
    
    agents_dir = tmp_path / ".agents"
    state_dir = agents_dir / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    with open(agents_dir / "permissions.json", "w") as f:
        json.dump({"initialized": True, "mode": "sandbox"}, f)
        
    # Mock subprocess.Popen and pid_exists to avoid starting real daemon
    with patch("subprocess.Popen") as mock_popen, \
         patch("psutil.pid_exists", return_value=True), \
         patch("workflow_runtime.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("workflow_runtime.get_version_info", return_value={"version": "1.0.0"}), \
         patch("validator.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("validator.get_version_info", return_value={"version": "1.0.0"}), \
         patch("drift.get_git_info", return_value={"is_git_repository": True, "branch": "main"}):
         
        # Simulate daemon running already
        with open(state_dir / "daemon.json", "w") as f:
            json.dump({"pid": 1234, "status": "running"}, f)
        with open(state_dir / "manager.json", "w") as f:
            json.dump({"manager_pid": 1235, "status": "healthy"}, f)
        with open(state_dir / "orchestrator.json", "w") as f:
            json.dump({"pid": 1234, "status": "running", "attach_mode": "started"}, f)
            
        args = ArgsMock()
        
        # First init -> should create policy file
        do_init(args)
        policy_path = get_runtime_policy_path()
        assert os.path.exists(policy_path)
        
        # Modify policy to custom values
        policy = load_runtime_policy(validate=True)
        policy["resource_limits"]["max_subagents"] = 12
        write_runtime_policy(policy)
        
        # Second init -> should reuse existing policy file and NOT overwrite it
        do_init(args)
        policy_reloaded = load_runtime_policy(validate=True)
        assert policy_reloaded["resource_limits"]["max_subagents"] == 12

def test_runtime_obeys_limits(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIWF_RUNTIME_POLICY_ROOT", str(tmp_path))
    
    # Initialize runtime
    rt = HierarchicalRuntime("FEAT-112")
    rt.state_dir = str(tmp_path)
    rt.agents = {}
    rt.task_graph = {"tasks": {}}
    rt.spawn_timestamps = []
    
    # Setup healthy policy
    load_runtime_policy(validate=True)
    
    with patch("psutil.cpu_percent", return_value=10.0), \
         patch("psutil.virtual_memory") as mock_mem:
        
        mock_mem.return_value.percent = 15.0
        
        # Test healthy state
        allowed, msg = rt.can_spawn_subagent("AGENT-001", "TASK-001")
        assert allowed is True
        assert msg == "READY"
        
        # Test CPU throttle
        with patch("psutil.cpu_percent", return_value=85.0):
            allowed, msg = rt.can_spawn_subagent("AGENT-001", "TASK-001")
            assert allowed is False
            assert "CPU too high" in msg
            
        # Test Memory throttle
        mock_mem.return_value.percent = 85.0
        allowed, msg = rt.can_spawn_subagent("AGENT-001", "TASK-001")
        assert allowed is False
        assert "Memory too high" in msg
        
        # Test Adaptive Concurrency
        mock_mem.return_value.percent = 75.0 # above warning limit (70)
        rt.task_graph["tasks"] = {
            "T1": {"status": "running"},
            "T2": {"status": "running"} # at warning load, concurrency limit adapted from 2 to 1
        }
        allowed, msg = rt.can_spawn_subagent("AGENT-001", "TASK-001")
        assert allowed is False
        assert "Concurrency limit exceeded" in msg

def test_cli_actions(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AIWF_RUNTIME_POLICY_ROOT", str(tmp_path))
    
    # Load defaults
    load_runtime_policy(validate=True)
    
    # Test display policy
    args = ArgsMock()
    args.subaction = "policy"
    do_runtime_action(args)
    captured = capsys.readouterr()
    assert "max_subagents" in captured.out
    
    # Test validate
    args.policy_action = "validate"
    do_runtime_action(args)
    captured = capsys.readouterr()
    assert "Validation PASSED" in captured.out
    
    # Test reset
    policy = load_runtime_policy(validate=True)
    policy["resource_limits"]["max_subagents"] = 80
    write_runtime_policy(policy)
    
    args.policy_action = "reset"
    do_runtime_action(args)
    captured = capsys.readouterr()
    assert "Successfully reset" in captured.out
    
    # Verify reset
    policy_reset = load_runtime_policy(validate=True)
    assert policy_reset["resource_limits"]["max_subagents"] == 4
