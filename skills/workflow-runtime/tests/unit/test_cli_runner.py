# test_cli_runner.py
import pytest
import os
import sys
import json
import warnings

# Add script directory to sys.path to find cli_runner, websocket_server, and runtime_sdk
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from cli_runner import CLIRunner
from websocket_server import RuntimeAPIServer
from runtime_sdk import RuntimeSDKv3

@pytest.mark.asyncio
async def test_cli_run_command():
    server = RuntimeAPIServer()
    sdk = RuntimeSDKv3(api_server=server)
    runner = CLIRunner(sdk=sdk)
    
    res = await runner.execute(["run"])
    assert "Session created" in res
    assert "Mode 1" in res

@pytest.mark.asyncio
async def test_cli_session_management():
    server = RuntimeAPIServer()
    sdk = RuntimeSDKv3(api_server=server)
    runner = CLIRunner(sdk=sdk)
    
    # 1. Create session via CLI
    res = await runner.execute(["session", "create", "--permission-mode", "sandbox"])
    data = json.loads(res)
    assert data["session_id"] == "session-new"
    
    # 2. Get status via CLI
    status_res = await runner.execute(["session", "status", "session-new"])
    status_data = json.loads(status_res)
    assert status_data["status"] == "ready"

@pytest.mark.asyncio
async def test_cli_session_follow():
    server = RuntimeAPIServer()
    sdk = RuntimeSDKv3(api_server=server)
    runner = CLIRunner(sdk=sdk)
    
    # Create session and write some mock events
    await sdk.create_session("session-follow-test")
    await sdk.create_agent("agent-plan", "session-follow-test", "Planner")
    
    res = await runner.execute(["session", "follow", "session-follow-test"])
    assert "TOPIC: session.created" in res
    assert "TOPIC: agent.created" in res

@pytest.mark.asyncio
async def test_legacy_orchestrator_deprecation():
    server = RuntimeAPIServer()
    sdk = RuntimeSDKv3(api_server=server)
    runner = CLIRunner(sdk=sdk)
    
    # Verify warning is raised for 'orchestrator start' legacy command
    with pytest.deprecated_call():
        res = await runner.execute(["orchestrator", "start"])
        assert "Compatibility Adapter" in res
