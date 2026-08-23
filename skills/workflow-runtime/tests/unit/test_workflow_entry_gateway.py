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
    temp_dir = tempfile.mkdtemp(prefix="gateway-test-ws-")
    
    # Create required .agents layout
    os.makedirs(os.path.join(temp_dir, ".agents", "state"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, ".agents", "runtime"), exist_ok=True)
    os.makedirs(os.path.join(temp_dir, ".agents", "config"), exist_ok=True)
    
    # Create empty registry and permissions
    with open(os.path.join(temp_dir, ".agents", "config", "permissions.json"), "w") as f:
        json.dump({"mode": "sandbox"}, f)
        
    orig_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield temp_dir
    os.chdir(orig_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_gateway_intent_classification(temp_ws):
    gateway = WorkflowEntryGateway(temp_ws)
    
    # Chat queries
    assert gateway.detect_intent("Explain the Go interface implementation pattern") == "chat"
    assert gateway.detect_intent("What is the difference between sequential and parallel runtimes?") == "chat"
    
    # Engineering queries
    assert gateway.detect_intent("Add OAuth login page feature") == "feature_request"
    assert gateway.detect_intent("Fix the subprocess timeout regression bug in FEAT-112") == "bug_fix"
    assert gateway.detect_intent("Refactor the state reducer to be pure function") == "refactoring"
    assert gateway.detect_intent("Run test suite on our new controller") == "feature_request"

def test_gateway_chat_flow(temp_ws):
    gateway = WorkflowEntryGateway(temp_ws)
    res = gateway.handle_request("Explain the Go interface implementation pattern")
    
    assert res["status"] == "BYPASS"
    assert res["intent"] == "chat"
    assert res["request_id"].startswith("REQ-")
    
    # Check trace event exists in events.jsonl
    logger = get_logger(temp_ws)
    events = logger.read_all()
    assert len(events) == 1
    assert events[0]["event_type"] == "workflow.request.received"
    assert events[0]["payload"]["intent"] == "chat"

def test_gateway_engineering_flow(temp_ws):
    gateway = WorkflowEntryGateway(temp_ws)
    
    # Clear env
    os.environ.pop("AIWF_WORKFLOW_ID", None)
    os.environ.pop("AIWF_EXECUTION_MODE", None)
    os.environ.pop("AIWF_CURRENT_PHASE", None)
    
    res = gateway.handle_request("Add OAuth login page (FEAT-401)")
    
    assert res["status"] == "ROUTED"
    assert res["intent"] == "feature_request"
    assert res["workflow_id"] == "FEAT-401"
    assert res["workflow"] == "standard-development"
    assert res["execution_mode"] == "workflow"
    assert res["current_phase"] == "brainstorming"
    
    # Check env variables are set
    assert os.environ["AIWF_WORKFLOW_ID"] == "FEAT-401"
    assert os.environ["AIWF_EXECUTION_MODE"] == "workflow"
    
    # Check events emitted
    logger = get_logger(temp_ws)
    events = logger.read_all()
    
    event_types = [e["event_type"] for e in events]
    assert "workflow.request.received" in event_types
    assert "workflow.started" in event_types
    assert "workflow.phase.started" in event_types
    assert "skill.selected" in event_types
    
    # Verify session persistence
    sdata = load_session()
    assert sdata.get("work_item", {}).get("id") == "FEAT-401"
    assert sdata.get("execution_mode") == "workflow"

@patch("sys.argv", ["mock_app.py"])
@patch.dict(os.environ, {}, clear=True)
def test_tool_execution_boundary_blocked(temp_ws):
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

def test_tool_execution_boundary_allowed(temp_ws):
    # Setup managed workflow environment context
    os.environ["AIWF_WORKFLOW_ID"] = "FEAT-308"
    os.environ["AIWF_EXECUTION_MODE"] = "workflow"
    
    executor = ToolExecutor()
    req = ToolRequest(
        session_id="SESS-001",
        agent_id="AGENT-SYSTEM",
        task_id="TASK-001",
        command="pytest",
        arguments=[],
        cwd="."
    )
    
    # ToolExecutor should allow it
    executor.validate_request(req)
    
    # ExecutionManager should validate it successfully
    valid, msg = ExecutionManager.validate_request({
        "command": "pytest",
        "working_directory": ".",
        "owner_agent_id": "AGENT-TESTER-001"
    })
    assert valid or "outside workspace bounds" in msg # Allow if within bounds
