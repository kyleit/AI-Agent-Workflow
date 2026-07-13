# runtime_sdk.py
import json
import asyncio
from typing import Any, Dict, List, Optional
from websocket_server import RuntimeAPIServer, ERROR_CODES

class SDKError(Exception):
    pass

class SessionNotFoundError(SDKError):
    pass

class PermissionDeniedError(SDKError):
    pass

class InvalidStateTransitionError(SDKError):
    pass

class TaskCancelledError(SDKError):
    pass

class ToolExecutionFailedError(SDKError):
    pass

class RuntimeSDKv3:
    def __init__(self, api_server: RuntimeAPIServer, token: str = "mock-token") -> None:
        self.api_server = api_server
        self.token = token
        self._req_id_counter = 1

    def _map_error(self, code: int, message: str) -> None:
        if code == ERROR_CODES["SESSION_NOT_FOUND"]:
            raise SessionNotFoundError(message)
        elif code == ERROR_CODES["PERMISSION_DENIED"]:
            raise PermissionDeniedError(message)
        elif code == ERROR_CODES["INVALID_STATE_TRANSITION"]:
            raise InvalidStateTransitionError(message)
        elif code == ERROR_CODES["TASK_CANCELLED"]:
            raise TaskCancelledError(message)
        elif code == ERROR_CODES["TOOL_EXECUTION_FAILED"]:
            raise ToolExecutionFailedError(message)
        else:
            raise SDKError(f"API Error [{code}]: {message}")

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Any:
        req_id = self._req_id_counter
        self._req_id_counter += 1

        # Simulate authentication integration
        params["auth_token"] = self.token

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": req_id
        }
        
        # In actual network SDK, this sends via websocket. 
        # In-process SDK directly routes to handle_request to avoid port collision.
        response_str = await self.api_server.handle_request(json.dumps(payload))
        response = json.loads(response_str)

        if "error" in response:
            err = response["error"]
            self._map_error(err["code"], err["message"])

        return response.get("result")

    # Scoped SDK APIs
    async def create_session(self, session_id: str, permission_mode: str = "sandbox") -> Dict[str, Any]:
        return await self._send_request(
            "create_session",
            {"session_id": session_id, "permission_mode": permission_mode}
        )

    async def load_session(self, session_id: str) -> Dict[str, Any]:
        return await self._send_request("load_session", {"session_id": session_id})

    async def submit_task(
        self,
        task_id: str,
        session_id: str,
        agent_id: str,
        requires_admin: bool = False
    ) -> Dict[str, Any]:
        return await self._send_request(
            "submit_task",
            {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "requires_admin": requires_admin
            }
        )

    async def create_agent(self, agent_id: str, session_id: str, role: str) -> Dict[str, Any]:
        return await self._send_request(
            "create_agent",
            {"agent_id": agent_id, "session_id": session_id, "role": role}
        )

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        return await self._send_request("get_agent_status", {"agent_id": agent_id})

    async def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        return await self._send_request("stream_session_events", {"session_id": session_id})
