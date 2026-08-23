# runtime_sdk.py
from __future__ import annotations

import json
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator


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
    def __init__(self, api_server: Any, token: str = "mock-token") -> None:
        self.api_server = api_server
        self.token = token
        self._req_id_counter = 1

    def _map_error(self, code: int, message: str) -> None:
        err_codes: dict[str, int] = cast(dict[str, int], getattr(InfrastructureLocator, "ERROR_CODES", {}))
        if code == err_codes.get("SESSION_NOT_FOUND", -1):
            raise SessionNotFoundError(message)
        elif code == err_codes.get("PERMISSION_DENIED", -2):
            raise PermissionDeniedError(message)
        elif code == err_codes.get("INVALID_STATE_TRANSITION", -3):
            raise InvalidStateTransitionError(message)
        elif code == err_codes.get("TASK_CANCELLED", -4):
            raise TaskCancelledError(message)
        elif code == err_codes.get("TOOL_EXECUTION_FAILED", -5):
            raise ToolExecutionFailedError(message)
        else:
            raise SDKError(f"API Error [{code}]: {message}")

    async def _send_request(self, method: str, params: dict[str, Any]) -> Any:
        req_id = self._req_id_counter
        self._req_id_counter += 1

        params["auth_token"] = self.token

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": req_id
        }

        handle_fn: Any = getattr(self.api_server, "handle_request", None)
        if callable(handle_fn):
            res_obj: Any = handle_fn(json.dumps(payload))
            if hasattr(res_obj, "__await__"):
                res_obj = await res_obj
            response_str = str(res_obj)
        else:
            response_str = "{}"
        raw_json = json.loads(response_str)
        response = cast(dict[str, Any], raw_json) if isinstance(raw_json, dict) else {}

        if "error" in response:
            err = cast(dict[str, Any], response["error"]) if isinstance(response["error"], dict) else {}
            code_val = int(str(err.get("code", 0)))
            msg_val = str(err.get("message", ""))
            self._map_error(code_val, msg_val)

        return response.get("result")

    async def create_session(self, session_id: str, permission_mode: str = "sandbox") -> dict[str, Any]:
        res = await self._send_request(
            "create_session",
            {"session_id": session_id, "permission_mode": permission_mode}
        )
        return cast(dict[str, Any], res) if isinstance(res, dict) else {}

    async def load_session(self, session_id: str) -> dict[str, Any]:
        res = await self._send_request("load_session", {"session_id": session_id})
        return cast(dict[str, Any], res) if isinstance(res, dict) else {}

    async def submit_task(
        self,
        task_id: str,
        session_id: str,
        agent_id: str,
        requires_admin: bool = False
    ) -> dict[str, Any]:
        res = await self._send_request(
            "submit_task",
            {
                "task_id": task_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "requires_admin": requires_admin
            }
        )
        return cast(dict[str, Any], res) if isinstance(res, dict) else {}

    async def create_agent(self, agent_id: str, session_id: str, role: str) -> dict[str, Any]:
        res = await self._send_request(
            "create_agent",
            {"agent_id": agent_id, "session_id": session_id, "role": role}
        )
        return cast(dict[str, Any], res) if isinstance(res, dict) else {}


__all__ = [
    "SDKError",
    "SessionNotFoundError",
    "PermissionDeniedError",
    "InvalidStateTransitionError",
    "TaskCancelledError",
    "ToolExecutionFailedError",
    "RuntimeSDKv3",
]
