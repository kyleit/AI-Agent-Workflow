"""WorkflowObservatoryHTTPHandler — HTTP handler for the workflow observatory.

Extracted from session_init_wizard.py to keep that file ≤500 lines (FIX-412 GATE-09).
"""
from __future__ import annotations

import http
import http.server
import json
import os
from typing import Any, Optional, cast


class WorkflowObservatoryHTTPHandler(http.server.BaseHTTPRequestHandler):
    workspace_override: Optional[str] = None

    def log_message(self, format: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        if self.path == '/api/workflow/current':
            _ = self.wfile.write(json.dumps(self.get_current_workflow(), indent=2).encode('utf-8'))
        elif self.path == '/api/workflow/events':
            _ = self.wfile.write(json.dumps(self.get_workflow_events(), indent=2).encode('utf-8'))
        elif self.path == '/api/workflow/agents':
            _ = self.wfile.write(json.dumps(self.get_workflow_agents(), indent=2).encode('utf-8'))
        elif self.path == '/api/workflow/skills':
            _ = self.wfile.write(json.dumps(self.get_workflow_skills(), indent=2).encode('utf-8'))
        elif self.path == '/api/workflow/gates':
            _ = self.wfile.write(json.dumps(self.get_workflow_gates(), indent=2).encode('utf-8'))
        else:
            _ = self.wfile.write(json.dumps({"error": "Not Found", "path": self.path}).encode('utf-8'))

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def get_current_workflow(self) -> dict[str, Any]:
        try:
            from workflow_runtime.infrastructure.session.state_store import (
                get_state_store)
            store = get_state_store()
            workflow = store.get("workflow") or {}
            context = store.get("context") or {}

            if not workflow:
                try:
                    from workflow_runtime.infrastructure.session.state_path import (
                        get_state_file)
                    with open(get_state_file("workflow", self.workspace_override), "r", encoding="utf-8") as f:
                        raw_wf = json.load(f)
                        workflow = cast(dict[str, Any], raw_wf) if isinstance(raw_wf, dict) else {}
                except Exception:
                    pass
            if not context:
                try:
                    from workflow_runtime.infrastructure.session.state_path import (
                        get_state_file)
                    with open(get_state_file("context", self.workspace_override), "r", encoding="utf-8") as f:
                        raw_ctx = json.load(f)
                        context = cast(dict[str, Any], raw_ctx) if isinstance(raw_ctx, dict) else {}
                except Exception:
                    pass

            raw_work_item = workflow.get("work_item")
            work_item_dict = cast(dict[str, Any], raw_work_item) if isinstance(raw_work_item, dict) else {}

            return {
                "workflow_id": workflow.get("active_workflow") or context.get("conversation_id") or "WF-DEFAULT",
                "feature_id": work_item_dict.get("id") or "FEAT-DEFAULT",
                "active_phase": workflow.get("active_phase") or "brainstorming",
                "checkpoint": workflow.get("checkpoint") or 1,
                "status": workflow.get("status") or "running",
                "progress_percentage": context.get("progress_percentage") or 10,
                "current_skill": workflow.get("suggested_next_skill") or "initialize-workflow",
                "waiting_for": workflow.get("waiting_for")
            }
        except Exception as e:
            return {"error": str(e)}

    def get_workflow_events(self) -> list[Any]:
        try:
            from workflow_runtime.infrastructure.session.state_path import (
                get_events_path)
            events_path = get_events_path(self.workspace_override)
        except Exception:
            events_path = os.path.join(".", ".agents", "state", "events", "events.jsonl")

        if not os.path.exists(events_path):
            return []
        events: list[Any] = []
        try:
            with open(events_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except Exception:
            pass
        return events

    def get_workflow_agents(self) -> dict[str, Any]:
        try:
            from workflow_runtime.infrastructure.session.state_store import (
                get_state_store)
            store = get_state_store()
            agents_data = store.get("agents") or {}

            if not agents_data:
                try:
                    from workflow_runtime.infrastructure.session.state_path import (
                        get_state_root)
                    state_root = get_state_root(self.workspace_override)
                    agents_path = os.path.join(state_root, "agents", "agents.json")
                    if os.path.exists(agents_path):
                        with open(agents_path, "r", encoding="utf-8") as f:
                            raw_ag = json.load(f)
                            agents_data = cast(dict[str, Any], raw_ag) if isinstance(raw_ag, dict) else {}
                except Exception:
                    pass

            return {
                "execution_mode": agents_data.get("execution_mode", "workflow"),
                "running_agents": agents_data.get("running_agents", []),
                "queued_agents": agents_data.get("queued_agents", []),
                "blocked_agents": agents_data.get("blocked_agents", []),
                "waiting_dependencies": agents_data.get("waiting_dependencies", [])
            }
        except Exception as e:
            return {"error": str(e)}

    def get_workflow_skills(self) -> dict[str, Any]:
        try:
            from workflow_runtime.infrastructure.session.state_store import (
                get_state_store)
            store = get_state_store()
            runtime = store.get("runtime") or {}

            if not runtime:
                try:
                    from workflow_runtime.infrastructure.session.state_path import (
                        get_state_root)
                    state_root = get_state_root(self.workspace_override)
                    runtime_path = os.path.join(state_root, "runtime", "runtime.json")
                    if os.path.exists(runtime_path):
                        with open(runtime_path, "r", encoding="utf-8") as f:
                            raw_rt = json.load(f)
                            runtime = cast(dict[str, Any], raw_rt) if isinstance(raw_rt, dict) else {}
                except Exception:
                    pass

            return {
                "current_skill": runtime.get("current_skill") or "initialize-workflow",
                "current_command": runtime.get("current_command") or "init",
                "current_step": runtime.get("current_step") or "Ready",
                "status": runtime.get("status") or "completed",
                "context_health": runtime.get("context_health") or "healthy",
                "current_logs": runtime.get("current_logs") or []
            }
        except Exception as e:
            return {"error": str(e)}

    def get_workflow_gates(self) -> dict[str, Any]:
        try:
            from workflow_runtime.infrastructure.session.state_store import (
                get_state_store)
            store = get_state_store()
            approvals = store.get("approvals") or {}

            if not approvals:
                from workflow_runtime.infrastructure.session.state_path import (
                    get_state_root)
                state_root = get_state_root(self.workspace_override)
                try:
                    approvals_path = os.path.join(state_root, "approvals", "approvals.json")
                    if os.path.exists(approvals_path):
                        with open(approvals_path, "r", encoding="utf-8") as f:
                            raw_app = json.load(f)
                            approvals = cast(dict[str, Any], raw_app) if isinstance(raw_app, dict) else {}
                except Exception:
                    pass
                if not approvals:
                    try:
                        gates_path = os.path.join(state_root, "gates", "gates.json")
                        if os.path.exists(gates_path):
                            with open(gates_path, "r", encoding="utf-8") as f:
                                raw_gates = json.load(f)
                                approvals = cast(dict[str, Any], raw_gates) if isinstance(raw_gates, dict) else {}
                    except Exception:
                        pass

            return {
                "blueprint": approvals.get("blueprint") or approvals.get("blueprint_gate") or {"exists": False, "approved": False},
                "specification": approvals.get("specification") or approvals.get("specification_gate") or {"exists": False, "approved": False},
                "release": approvals.get("release") or approvals.get("release_gate") or {"exists": False, "approved": False}
            }
        except Exception as e:
            return {"error": str(e)}


__all__ = ["WorkflowObservatoryHTTPHandler"]
