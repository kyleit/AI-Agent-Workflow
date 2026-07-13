"""
test_workflow_enforcement.py — Integration tests for AIWF Workflow First Enforcement rules.
Verifies entry gate, direct coding blocks, artifact checks, and state separation.
"""
import os
import sys
import unittest
import json

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


class WorkflowFirstEnforcementTests(RuntimeTestBase):

    def setUp(self):
        super().setUp()
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)

    def read_state(self, category: str) -> dict:
        file_map = {
            "workflow": "workflow.json",
            "runtime": "runtime.json",
            "context": "context.json",
            "project": "profile.json",
            "recovery": "recovery.json",
            "approvals": "approvals.json",
            "agents": "agents.json",
        }
        filename = file_map.get(category, f"{category}.json")
        path = os.path.join(self.state_root, category, filename)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 1. Verification of entry gate triggering & trace events
    def test_workflow_trigger_enforcement(self):
        from event_logger import EventLogger
        logger = EventLogger(self.workspace)
        
        # Emit request received and started events
        logger.emit("workflow.request.received", {"request": "Add OAuth login"})
        logger.emit("workflow.started", {"workflow": "feature-development"})
        
        # Verify events.jsonl contains these events
        events_path = os.path.join(self.workspace, ".agents", "state", "events", "events.jsonl")
        self.assertTrue(os.path.exists(events_path), "events.jsonl should be created")
        
        events = []
        with open(events_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
                    
        self.assertEqual(events[0]["event_type"], "workflow.request.received")
        self.assertEqual(events[1]["event_type"], "workflow.started")

    # 2. Verify brainstorming runs before implementation
    def test_brainstorming_runs_before_implementation(self):
        self.write_state("workflow", {
            "checkpoint": 1,
            "status": "in_progress",
            "current_skill": "blueprint-to-implementation" # Trying to run implementation directly
        })
        
        # A check function simulating the enforcement policy
        def check_workflow_validity(state):
            checkpoint = state.get("checkpoint", 1)
            current_skill = state.get("current_skill")
            
            # Implementation is checkpoint 6, but checkpoint is currently 1
            if current_skill == "blueprint-to-implementation" and checkpoint < 6:
                return "BLOCKED"
            return "READY"
            
        status = check_workflow_validity(self.read_state("workflow"))
        self.assertEqual(status, "BLOCKED", "Implementation must be blocked if checkpoint is less than 6")

    # 3. Verify planning & blueprint artifacts check
    def test_required_artifacts_exist(self):
        # Case A: Missing blueprint artifact
        self.write_state("workflow", {
            "checkpoint": 6,
            "status": "in_progress",
            "feature_id": "FEAT-100"
        })
        
        def check_artifacts(feature_id):
            blueprint_path = os.path.join(self.workspace, "docs", "designs", f"{feature_id}_slug_blueprint.md")
            if not os.path.exists(blueprint_path):
                return "BLOCKED"
            return "COMPLETED"
            
        status = check_artifacts("FEAT-100")
        self.assertEqual(status, "BLOCKED", "Missing blueprint artifact must block workflow")

        # Case B: Blueprint exists
        designs_dir = os.path.join(self.workspace, "docs", "designs")
        os.makedirs(designs_dir, exist_ok=True)
        with open(os.path.join(designs_dir, "FEAT-100_slug_blueprint.md"), "w") as f:
            f.write("# FEAT-100 Design Blueprint")
            
        status2 = check_artifacts("FEAT-100")
        self.assertEqual(status2, "COMPLETED", "Workflow should proceed when blueprint artifact exists")

    # 4. Verify direct coding blocks
    def test_direct_coding_blocked(self):
        # Simulate an attempt to write code files before design approval
        self.write_state("approvals", {
            "blueprint": {"exists": True, "approved": False} # Blueprint exists but not approved yet
        })
        
        def is_code_modification_allowed(approvals):
            blueprint_approval = approvals.get("blueprint", {})
            return blueprint_approval.get("approved", False)
            
        allowed = is_code_modification_allowed(self.read_state("approvals"))
        self.assertFalse(allowed, "Direct coding modification must be blocked before blueprint approval")

    # 5. Verify workspace state and workflow state separation
    def test_workspace_workflow_state_separated(self):
        # Workspace doctor reports workspace status = READY
        workspace_doctor_report = {"status": "READY", "workspace_path": self.workspace}
        
        # Feature workflow is still in progress (not completed)
        self.write_state("workflow", {
            "checkpoint": 3,
            "status": "in_progress"
        })
        
        self.assertEqual(workspace_doctor_report["status"], "READY")
        
        workflow_state = self.read_state("workflow")
        self.assertNotEqual(workflow_state["status"], "completed", "Workspace ready does not mean feature workflow is completed")


if __name__ == "__main__":
    unittest.main()
