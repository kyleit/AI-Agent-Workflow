"""
test_extension_workflow_observatory.py — Integration tests for V2 Workflow Observatory API endpoints.
Verifies the response structure, response code, and non-blocking state access of HTTP API Server.
"""
import os
import sys
import unittest
import threading
import urllib.request
import json
from http.server import HTTPServer

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

import importlib.util
fixtures_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures"))
spec = importlib.util.spec_from_file_location("fixtures_conftest", os.path.join(fixtures_dir, "conftest.py"))
if spec and spec.loader:
    fixtures_conftest = importlib.util.module_from_spec(spec)
    sys.modules["fixtures_conftest"] = fixtures_conftest
    spec.loader.exec_module(fixtures_conftest)
    RuntimeTestBase = fixtures_conftest.RuntimeTestBase
else:
    raise ImportError("Could not load fixtures/conftest.py")

from workflow_runtime import WorkflowObservatoryHTTPHandler


class MockArgs:
    def __init__(self, workspace, port, host="127.0.0.1"):
        self.workspace = workspace
        self.port = port
        self.host = host


class ExtensionWorkflowObservatoryTests(RuntimeTestBase):
    server = None
    server_thread = None
    port = 31088

    @classmethod
    def setUpClass(cls):
        # We need a shared state dir setup, but setUpClass doesn't have self.workspace yet.
        pass

    def setUp(self):
        super().setUp()
        # Initialize subfolders in workspace for mock state
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)

        # Write dummy state files so that the HTTP API Server does not fail
        self.write_state("workflow", {
            "checkpoint": 1,
            "status": "in_progress",
            "current_skill": "initialize-workflow",
            "active_skill": "initialize-workflow",
            "active_command": "init",
            "active_agent": "architect",
            "current_logs": ["> Scanning workspace...", "> Ready"],
            "suggested_next_skill": "initialize-workflow"
        })
        self.write_state("agents", {
            "running_agents": [{"agent_id": "architect", "role": "Architect", "status": "running"}]
        })
        self.write_state("runtime", {
            "context_health": "healthy"
        })
        self.write_state("approvals", {
            "specification_gate": {"exists": True, "approved": True, "approved_by": "Ba"},
            "blueprint_gate": {"exists": True, "approved": False},
            "release_gate": {"exists": False, "approved": False}
        })

        # Set up events.jsonl
        events_dir = os.path.join(self.workspace, ".agents", "state", "events")
        os.makedirs(events_dir, exist_ok=True)
        events_path = os.path.join(events_dir, "events.jsonl")
        with open(events_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"event_type": "workflow_start", "timestamp": "2026-07-13T12:00:00Z", "skill": "initialize-workflow", "checkpoint": 1}) + "\n")

        # Start HTTP API Server on port 31088
        handler_class = WorkflowObservatoryHTTPHandler
        # Bind workspace to handler
        handler_class.workspace_override = self.workspace

        self.server = HTTPServer(("127.0.0.1", self.port), handler_class)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def tearDown(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread:
            self.server_thread.join(timeout=1.0)
        super().tearDown()

    def fetch_api(self, endpoint):
        url = f"http://127.0.0.1:{self.port}{endpoint}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2.0) as response:
            self.assertEqual(response.status, 200)
            data = response.read().decode("utf-8")
            return json.loads(data)

    def test_api_current(self):
        data = self.fetch_api("/api/workflow/current")
        self.assertIn("checkpoint", data)
        self.assertEqual(data["checkpoint"], 1)
        self.assertEqual(data["current_skill"], "initialize-workflow")

    def test_api_events(self):
        data = self.fetch_api("/api/workflow/events")
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["event_type"], "workflow_start")

    def test_api_agents(self):
        data = self.fetch_api("/api/workflow/agents")
        self.assertIn("running_agents", data)
        self.assertEqual(len(data["running_agents"]), 1)
        self.assertEqual(data["running_agents"][0]["agent_id"], "architect")

    def test_api_skills(self):
        data = self.fetch_api("/api/workflow/skills")
        self.assertIn("context_health", data)
        self.assertEqual(data["context_health"], "healthy")

    def test_api_gates(self):
        data = self.fetch_api("/api/workflow/gates")
        self.assertIn("specification", data)
        self.assertTrue(data["specification"]["approved"])
        self.assertFalse(data["blueprint"]["approved"])


if __name__ == "__main__":
    unittest.main()
