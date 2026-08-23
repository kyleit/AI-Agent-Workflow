import os
import sys
import pytest
import json
import shutil
import tempfile
from unittest.mock import patch

# Add scripts directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from workflow_entry_gateway import WorkflowEntryGateway
from external_executor import ToolExecutor, ToolRequest
from execution_manager import ExecutionManager
from event_logger import get_logger
from session import load_session

@pytest.fixture
def temp_ws():
    # Setup temporary mock workspace
    temp_dir = tempfile.mkdtemp(prefix="gateway-enforce-test-ws-")
    
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

def test_natural_language_request(temp_ws):
    # Setup gateway
    gateway = WorkflowEntryGateway(temp_ws)
    
    # Clear env
    os.environ.pop("AIWF_WORKFLOW_ID", None)
    os.environ.pop("AIWF_EXECUTION_MODE", None)
    os.environ.pop("AIWF_CURRENT_PHASE", None)
    
    # Handle natural language request
    res = gateway.handle_request("Add Google OAuth login")
    
    assert res["status"] == "ROUTED"
    assert res["intent"] == "feature_request"
    assert res["workflow_id"].startswith("FEAT-")
    assert res["workflow"] == "standard-development"
    assert res["next_skill"] == "brainstorming"
    
    # Simulate automatic brainstorming invocation & document generation
    doc_path = os.path.join(temp_ws, "docs", "brainstorming", f"{res['workflow_id']}_google_oauth_login.md")
    with open(doc_path, "w") as f:
        f.write("# Spec: Google OAuth Login")
    
    # Verify file generated
    assert os.path.exists(doc_path)
    
    # Check trace events exist in events.jsonl
    logger = get_logger(temp_ws)
    events = logger.read_all()
    
    event_types = [e["event_type"] for e in events]
    assert "workflow.request.received" in event_types
    assert "workflow.created" in event_types
    assert "workflow.started" in event_types
    assert "skill.selected" in event_types
    assert "skill.started" in event_types

@patch("sys.argv", ["mock_app.py"])
@patch.dict(os.environ, {}, clear=True)
def test_direct_execution_attempt(temp_ws):
    # Setup unmanaged scenario (no workflow environment context)
    executor = ToolExecutor()
    req = ToolRequest(
        session_id="SESS-001",
        agent_id="AGENT-SYSTEM",
        task_id="TASK-001",
        command="pytest",
        arguments=[]
    )
    
    # ToolExecutor should block direct tool execution
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

def test_skill_execution_chain(temp_ws):
    gateway = WorkflowEntryGateway(temp_ws)
    res = gateway.handle_request("Add Google OAuth login")
    
    # Verify starting phase is brainstorming
    assert res["next_skill"] == "brainstorming"
    
    # Verify session context is initialized
    sdata = load_session()
    assert sdata.get("work_item", {}).get("id") == res["workflow_id"]
    assert sdata.get("execution_mode") == "workflow"
    assert sdata.get("active_phase") == "brainstorming"
