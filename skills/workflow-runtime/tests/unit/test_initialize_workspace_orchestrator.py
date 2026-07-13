import os
import json
import pytest
import sys
import subprocess
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from workflow_runtime import do_init
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

# Setup custom popen that only mocks the daemon startup Popen call
orig_popen = subprocess.Popen
def custom_popen_factory(state_dir):
    def custom_popen(args, *pargs, **kwargs):
        if isinstance(args, list) and len(args) > 1 and "hierarchical_runtime.py" in args[1]:
            # Simulate daemon writing its files
            with open(state_dir / "daemon.json", "w") as f:
                json.dump({"pid": 1234, "status": "running"}, f)
            with open(state_dir / "manager.json", "w") as f:
                json.dump({"manager_pid": 1235, "status": "healthy"}, f)
            with open(state_dir / "orchestrator.json", "w") as f:
                json.dump({"pid": 1234, "status": "running", "attach_mode": "started"}, f)
            
            mock_p = MagicMock()
            mock_p.communicate.return_value = (b"", b"")
            mock_p.returncode = 0
            mock_p.__enter__.return_value = mock_p
            return mock_p
        return orig_popen(args, *pargs, **kwargs)
    return custom_popen

def custom_pid_exists(pid):
    if pid in [1234, 1235]:
        return True
    return False

def test_do_init_first_invocation(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    
    # Pre-setup permissions and profiles
    agents_dir = tmp_path / ".agents"
    state_dir = agents_dir / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    with open(agents_dir / "permissions.json", "w") as f:
        json.dump({"initialized": True, "mode": "sandbox"}, f)
        
    mock_proc = MagicMock()
    mock_proc.create_time.return_value = 1783900000.0
    mock_proc.is_running.return_value = True
        
    with patch("subprocess.Popen", side_effect=custom_popen_factory(state_dir)), \
         patch("psutil.pid_exists", side_effect=custom_pid_exists), \
         patch("psutil.Process", return_value=mock_proc), \
         patch("workflow_runtime.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("workflow_runtime.get_version_info", return_value={"version": "1.0.0"}), \
         patch("validator.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("validator.get_version_info", return_value={"version": "1.0.0"}), \
         patch("drift.get_git_info", return_value={"is_git_repository": True, "branch": "main"}):
         
        args = ArgsMock()
        do_init(args)
        
        captured = capsys.readouterr()
        assert "Runtime Manager: STARTED" in captured.out
        assert "Resident Orchestrator: STARTED" in captured.out
        assert "Attach Mode: started" in captured.out
        assert "Status: READY" in captured.out

def test_do_init_second_invocation_attach(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    
    agents_dir = tmp_path / ".agents"
    state_dir = agents_dir / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    with open(agents_dir / "permissions.json", "w") as f:
        json.dump({"initialized": True, "mode": "sandbox"}, f)
        
    # Pre-create running daemon info to simulate running daemon
    with open(state_dir / "daemon.json", "w") as f:
        json.dump({"pid": 1234, "status": "running"}, f)
    with open(state_dir / "manager.json", "w") as f:
        json.dump({"manager_pid": 1235, "status": "healthy"}, f)
    with open(state_dir / "orchestrator.json", "w") as f:
        json.dump({"pid": 1234, "status": "running", "attach_mode": "started", "process_create_time": 1783900000.0}, f)
        
    mock_proc = MagicMock()
    mock_proc.create_time.return_value = 1783900000.0
    mock_proc.is_running.return_value = True
        
    with patch("subprocess.Popen") as mock_popen, \
         patch("psutil.pid_exists", side_effect=custom_pid_exists), \
         patch("psutil.Process", return_value=mock_proc), \
         patch("workflow_runtime.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("workflow_runtime.get_version_info", return_value={"version": "1.0.0"}), \
         patch("validator.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("validator.get_version_info", return_value={"version": "1.0.0"}), \
         patch("drift.get_git_info", return_value={"is_git_repository": True, "branch": "main"}):
          
        args = ArgsMock()
        do_init(args)
        
        captured = capsys.readouterr()
        
        # Verify it did not try to start the daemon process
        for call in mock_popen.call_args_list:
            call_args = call[0][0]
            if isinstance(call_args, list) and len(call_args) > 1 and "hierarchical_runtime.py" in call_args[1]:
                pytest.fail("Should not start another daemon process on attach!")
                
        assert "Runtime Manager: REUSED" in captured.out or "Runtime Manager: RUNNING" in captured.out
        assert "Resident Orchestrator: ATTACHED" in captured.out or "Resident Orchestrator: RUNNING" in captured.out
        assert "Attach Mode: attached" in captured.out or "Attach Mode: started" in captured.out
        assert "Status: READY" in captured.out

def test_do_init_startup_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    
    agents_dir = tmp_path / ".agents"
    state_dir = agents_dir / "state"
    os.makedirs(state_dir, exist_ok=True)
    
    with open(agents_dir / "permissions.json", "w") as f:
        json.dump({"initialized": True, "mode": "sandbox"}, f)
        
    # Setup custom popen that does NOT write daemon files to simulate startup failure
    def custom_popen_fail(args, *pargs, **kwargs):
        if isinstance(args, list) and len(args) > 1 and "hierarchical_runtime.py" in args[1]:
            mock_p = MagicMock()
            mock_p.communicate.return_value = (b"", b"")
            mock_p.returncode = 0
            mock_p.__enter__.return_value = mock_p
            return mock_p
        return orig_popen(args, *pargs, **kwargs)
        
    with patch("subprocess.Popen", side_effect=custom_popen_fail), \
         patch("psutil.pid_exists", return_value=False), \
         patch("workflow_runtime.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("workflow_runtime.get_version_info", return_value={"version": "1.0.0"}), \
         patch("validator.get_git_info", return_value={"is_git_repository": True, "branch": "main"}), \
         patch("validator.get_version_info", return_value={"version": "1.0.0"}), \
         patch("drift.get_git_info", return_value={"is_git_repository": True, "branch": "main"}):
         
        args = ArgsMock()
        with pytest.raises(SystemExit) as e:
            do_init(args)
            
        assert e.value.code == 1
        captured = capsys.readouterr()
        assert "INITIALIZATION FAILED" in captured.out
        assert "Resident Orchestrator: NOT RUNNING" in captured.out
