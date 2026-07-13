# websocket_server.py
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

ERROR_CODES = {
    "SESSION_NOT_FOUND": -32001,
    "PERMISSION_DENIED": -32002,
    "INVALID_STATE_TRANSITION": -32003,
    "TASK_CANCELLED": -32004,
    "TOOL_EXECUTION_FAILED": -32005
}

class JSONRPCError(Exception):
    def __init__(self, code_name: str, message: str) -> None:
        self.code = ERROR_CODES.get(code_name, -32603)
        self.code_name = code_name
        self.message = message
        super().__init__(message)

class RuntimeAPIServer:
    def __init__(self) -> None:
        self.sessions: Dict[str, Any] = {}
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.event_queues: Dict[str, List[Dict[str, Any]]] = {}

    async def handle_request(self, request_str: str) -> str:
        try:
            req = json.loads(request_str)
        except json.JSONDecodeError:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})

        # Validate JSON-RPC 2.0 structure
        if req.get("jsonrpc") != "2.0" or "method" not in req or "id" not in req:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": req.get("id")})

        method = req["method"]
        params = req.get("params", {})
        req_id = req["id"]

        try:
            result = await self.dispatch(method, params)
            return json.dumps({"jsonrpc": "2.0", "result": result, "id": req_id})
        except JSONRPCError as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "error": {"code": e.code, "message": e.message, "data": {"code_name": e.code_name}},
                "id": req_id
            })
        except Exception as e:
            return json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": req_id})

    async def dispatch(self, method: str, params: Dict[str, Any]) -> Any:
        # Session Management APIs
        if method == "create_session":
            session_id = params.get("session_id") or "session-uuid"
            self.sessions[session_id] = {
                "session_id": session_id,
                "status": "ready",
                "permission_mode": params.get("permission_mode", "sandbox")
            }
            self.event_queues[session_id] = []
            self.record_event(session_id, "session.created", {"session_id": session_id})
            return {"session_id": session_id, "status": "ready"}
            
        elif method == "load_session":
            s_id = params.get("session_id")
            if s_id not in self.sessions:
                raise JSONRPCError("SESSION_NOT_FOUND", f"Session '{s_id}' does not exist.")
            return self.sessions[s_id]

        elif method == "close_session":
            s_id = params.get("session_id")
            if s_id not in self.sessions:
                raise JSONRPCError("SESSION_NOT_FOUND", f"Session '{s_id}' does not exist.")
            self.sessions[s_id]["status"] = "completed"
            self.record_event(s_id, "session.completed", {"session_id": s_id})
            return True

        # Task Management APIs
        elif method == "submit_task":
            t_id = params.get("task_id") or "task-uuid"
            s_id = params.get("session_id")
            if s_id not in self.sessions:
                raise JSONRPCError("SESSION_NOT_FOUND", f"Session '{s_id}' does not exist.")
            
            # Simple permission check integration
            if self.sessions[s_id]["permission_mode"] == "restricted" and params.get("requires_admin"):
                raise JSONRPCError("PERMISSION_DENIED", "Task requires higher permission level.")

            task = {
                "task_id": t_id,
                "session_id": s_id,
                "agent_id": params.get("agent_id"),
                "status": "queued",
                "dependencies": params.get("dependencies", [])
            }
            self.tasks[t_id] = task
            self.record_event(s_id, "task.queued", {"task_id": t_id})
            return task

        elif method == "query_task":
            t_id = params.get("task_id")
            if t_id not in self.tasks:
                return None
            return self.tasks[t_id]

        # Logical Agent Management APIs
        elif method == "create_agent":
            a_id = params.get("agent_id") or "agent-uuid"
            s_id = params.get("session_id")
            if s_id not in self.sessions:
                raise JSONRPCError("SESSION_NOT_FOUND", f"Session '{s_id}' does not exist.")

            agent = {
                "agent_id": a_id,
                "session_id": s_id,
                "role": params.get("role"),
                "status": "declared"
            }
            self.agents[a_id] = agent
            self.record_event(s_id, "agent.created", {"agent_id": a_id})
            return agent

        elif method == "get_agent_status":
            a_id = params.get("agent_id")
            if a_id not in self.agents:
                return None
            return self.agents[a_id]

        # Event Streaming API
        elif method == "stream_session_events":
            s_id = params.get("session_id")
            if s_id not in self.sessions:
                raise JSONRPCError("SESSION_NOT_FOUND", f"Session '{s_id}' does not exist.")
            return self.event_queues.get(s_id, [])

        else:
            raise JSONRPCError("INVALID_STATE_TRANSITION", f"Method '{method}' not found.")

    def record_event(self, session_id: str, topic: str, payload: Dict[str, Any]) -> None:
        if session_id in self.event_queues:
            event = {
                "topic": topic,
                "payload": payload,
                "timestamp": datetime.now().astimezone().isoformat()
            }
            self.event_queues[session_id].append(event)
