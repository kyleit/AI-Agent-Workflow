# test_websocket_server.py
import pytest
import os
import sys
import warnings

# Add script directory to sys.path to find websocket_server, runtime_sdk, and compatibility_adapter
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from websocket_server import RuntimeAPIServer, JSONRPCError
from runtime_sdk import RuntimeSDKv3, SessionNotFoundError, PermissionDeniedError
from compatibility_adapter import CompatibilityAdapterV1toV3

@pytest.mark.asyncio
async def test_api_server_session_creation():
    server = RuntimeAPIServer()
    
    # Test valid create_session JSON-RPC request
    req = {
        "jsonrpc": "2.0",
        "method": "create_session",
        "params": {"session_id": "session-123"},
        "id": 1
    }
    
    import json
    response_str = await server.handle_request(json.dumps(req))
    response = json.loads(response_str)
    
    assert response["jsonrpc"] == "2.0"
    assert response["result"]["session_id"] == "session-123"
    assert response["id"] == 1
    
    # Test load nonexistent session
    req_load = {
        "jsonrpc": "2.0",
        "method": "load_session",
        "params": {"session_id": "nonexistent"},
        "id": 2
    }
    response_load_str = await server.handle_request(json.dumps(req_load))
    response_load = json.loads(response_load_str)
    
    assert "error" in response_load
    assert response_load["error"]["code"] == -32001
    assert response_load["error"]["data"]["code_name"] == "SESSION_NOT_FOUND"

@pytest.mark.asyncio
async def test_sdk_error_mapping():
    server = RuntimeAPIServer()
    sdk = RuntimeSDKv3(api_server=server)
    
    # Test session not found error mapping
    with pytest.raises(SessionNotFoundError):
        await sdk.load_session("nonexistent-session")
        
    # Create session and test permission denied error mapping
    await sdk.create_session("session-abc", permission_mode="restricted")
    with pytest.raises(PermissionDeniedError):
        # Requesting admin task in restricted session should raise PermissionDeniedError
        await sdk.submit_task("task-1", "session-abc", "agent-1", requires_admin=True)

@pytest.mark.asyncio
async def test_compatibility_adapter_warnings():
    server = RuntimeAPIServer()
    sdk = RuntimeSDKv3(api_server=server)
    adapter = CompatibilityAdapterV1toV3(sdk_v3=sdk)
    
    # Create session
    await sdk.create_session("session-v1")
    
    # Check that calling load_session_v1 triggers a DeprecationWarning
    with pytest.deprecated_call():
        res = await adapter.load_session_v1("session-v1")
        assert res["session_id"] == "session-v1"
