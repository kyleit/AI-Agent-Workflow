import os
import sys
import pytest
import json
import shutil
import tempfile
from unittest.mock import patch

# Add scripts and adapters directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "adapters")))

from antigravity_gateway import AntigravityGatewayAdapter
from session_bootstrap_guard import SessionBootstrapGuard
from external_executor import ToolExecutor, ToolRequest
from execution_manager import ExecutionManager
from session import load_session

@pytest.fixture
def temp_ws():
    # Setup temporary mock workspace
    temp_dir = tempfile.mkdtemp(prefix="antigravity-adapter-test-ws-")
    
    # Create required .agents layout
    os.makedirs(os.path.join(temp_dir, ".agents", "state"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, ".agents", "runtime"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, ".agents", "config"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, "docs", "brainstorming"), exist_ok=True)
    
    # Create empty registry and permissions
    with open(os.path.join(temp_dir, ".agents", "config", "permissions.json"), "w") as f:
        json.dump({"mode": "sandbox"}, f)
        
    orig_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(orig_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_feature_request_flow(temp_ws):
    # Clear env context
    os.environ.pop("AIWF_WORKFLOW_ID", None)
    os.environ.pop("AIWF_EXECUTION_MODE", None)
    os.environ.pop("AIWF_CURRENT_PHASE", None)
    os.environ.pop("AIWF_TESTING", None)
    
    adapter = AntigravityGatewayAdapter(temp_ws)
    
    # Submit feature request
    res = adapter.submit_workflow("Add Google OAuth login", "SESS-ANTIGRAVITY-001")
    
    # Assert return format compliance
    assert res["status"] == "STARTED"
    assert res["phase"] == "brainstorming"
    assert res["workflow_id"].startswith("FEAT-")
    
    # Verify brainstorming document generated
    brainstorm_doc = os.path.join(temp_ws, "docs", "brainstorming", f"{res['workflow_id']}.md")
    assert os.path.exists(brainstorm_doc)
    
    # Check session state context injection
    session_data = load_session()
    assert session_data.get("execution_mode") == "workflow"
    assert session_data.get("source") == "antigravity"
    assert session_data.get("session_id") == "SESS-ANTIGRAVITY-001"
    
    # Verify environment variables set
    assert os.environ.get("AIWF_EXECUTION_MODE") == "workflow"
    assert os.environ.get("AIWF_SOURCE") == "antigravity"
    assert os.environ.get("AIWF_SESSION_ID") == "SESS-ANTIGRAVITY-001"

@patch("sys.argv", ["mock_app.py"])
@patch.dict(os.environ, {}, clear=True)
def test_direct_coding_block(temp_ws):
    # Ensure env variables are cleared (simulate no workflow context)
    os.environ.pop("AIWF_WORKFLOW_ID", None)
    os.environ.pop("AIWF_EXECUTION_MODE", None)
    os.environ.pop("AIWF_TESTING", None)
    
    # Delete local session file to simulate fresh unmanaged workspace
    sess_file = os.path.join(temp_ws, ".agents", ".session.json")
    if os.path.exists(sess_file):
        os.remove(sess_file)

    # ToolExecutor should raise PermissionError with EXECUTION_BLOCKED
    executor = ToolExecutor()
    req = ToolRequest(
        session_id="SESS-002",
        agent_id="AGENT-SYSTEM",
        task_id="TASK-002",
        command="pytest",
        arguments=[]
    )
    
    with pytest.raises(PermissionError) as exc_info:
        executor.validate_request(req)
    assert "EXECUTION_BLOCKED" in str(exc_info.value)

    # ExecutionManager should block unmanaged execution
    valid, msg = ExecutionManager.validate_request({
        "command": "pytest",
        "working_directory": "."
    })
    assert not valid
    assert "EXECUTION_BLOCKED" in msg

def test_session_reuse(temp_ws):
    # Initialize adapter
    adapter = AntigravityGatewayAdapter(temp_ws)
    
    # Submitting first task bootstrap session
    res1 = adapter.submit_workflow("Add dark mode support", "SESS-ANTIGRAVITY-002")
    assert res1["status"] == "STARTED"
    
    # Verify bootstrap guard shows initialized
    guard = SessionBootstrapGuard(temp_ws, "SESS-ANTIGRAVITY-002")
    assert guard.is_initialized()
    
    # Submitting second task should skip bootstrap step and reuse session successfully
    res2 = adapter.submit_workflow("Fix sidebar contrast bug", "SESS-ANTIGRAVITY-002")
    assert res2["status"] == "STARTED"
    assert res2["workflow_id"].startswith("FEAT-")
