import os
import sys
import pytest
import json
import shutil
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from session_bootstrap_guard import SessionBootstrapGuard

@pytest.fixture
def temp_ws():
    temp_dir = tempfile.mkdtemp(prefix="session-guard-test-ws-")
    orig_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(orig_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_first_request_initializes(temp_ws):
    guard = SessionBootstrapGuard(temp_ws, "session-A")
    assert not guard.is_initialized()
    
    # Initialize workspace
    success, err = guard.initialize_workspace()
    assert success
    assert not err
    
    # Check initialized state persisted
    assert guard.is_initialized()
    
    session_file = os.path.join(temp_ws, ".agents", "state", "sessions", "session-A.json")
    assert os.path.exists(session_file)
    with open(session_file, "r") as f:
        data = json.load(f)
        assert data["initialized"] is True
        assert data["workspace_ready"] is True
        assert data["runtime_ready"] is True

def test_session_isolation(temp_ws):
    guard_a = SessionBootstrapGuard(temp_ws, "session-A")
    guard_b = SessionBootstrapGuard(temp_ws, "session-B")
    
    assert not guard_a.is_initialized()
    assert not guard_b.is_initialized()
    
    guard_a.initialize_workspace()
    
    assert guard_a.is_initialized()
    assert not guard_b.is_initialized()

def test_failed_initialization_on_write_error(temp_ws):
    # Mocking write failure by making .agents read-only
    guard = SessionBootstrapGuard(temp_ws, "session-A")
    
    # Pre-create directory and make it read-only
    agents_dir = os.path.join(temp_ws, ".agents")
    os.makedirs(agents_dir, exist_ok=True)
    os.chmod(agents_dir, 0o400) # Read only
    
    # Should return failure
    success, err = guard.initialize_workspace()
    assert not success
    assert err != ""
    
    # Clean permissions so temp_ws can be deleted
    os.chmod(agents_dir, 0o700)

def test_cli_session_commands(temp_ws):
    from workflow_runtime import main
    import sys
    from unittest.mock import patch
    from io import StringIO
    
    # 1. status check (initialized should be false)
    with patch.object(sys, "argv", ["workflow_runtime.py", "session", "status", "--session-id", "session-A"]):
        stdout = StringIO()
        with patch.object(sys, "stdout", stdout):
            main()
        res = json.loads(stdout.getvalue())
        assert res["session_id"] == "session-A"
        assert res["initialized"] is False
        
    # 2. initialize session
    with patch.object(sys, "argv", ["workflow_runtime.py", "session", "initialize", "--session-id", "session-A"]):
        stdout = StringIO()
        with patch.object(sys, "stdout", stdout):
            main()
        res = json.loads(stdout.getvalue())
        assert res["session_id"] == "session-A"
        assert res["initialized"] is True
        assert res["workspace_ready"] is True
        
    # 3. status check (initialized should be true)
    with patch.object(sys, "argv", ["workflow_runtime.py", "session", "status", "--session-id", "session-A"]):
        stdout = StringIO()
        with patch.object(sys, "stdout", stdout):
            main()
        res = json.loads(stdout.getvalue())
        assert res["initialized"] is True
        
    # 4. reset session
    with patch.object(sys, "argv", ["workflow_runtime.py", "session", "reset", "--session-id", "session-A"]):
        stdout = StringIO()
        with patch.object(sys, "stdout", stdout):
            main()
        assert "reset successfully" in stdout.getvalue()

    # 5. status check after reset (initialized should be false)
    with patch.object(sys, "argv", ["workflow_runtime.py", "session", "status", "--session-id", "session-A"]):
        stdout = StringIO()
        with patch.object(sys, "stdout", stdout):
            main()
        res = json.loads(stdout.getvalue())
        assert res["initialized"] is False

