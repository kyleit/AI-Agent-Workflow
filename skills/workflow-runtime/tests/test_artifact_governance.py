# test_artifact_governance.py
import os
import shutil
import unittest
from artifact_governance import ArtifactGovernance
from workflow_supervisor import WorkflowSupervisor
from workflow_state_machine import WorkflowStateMachine

class TestArtifactGovernance(unittest.TestCase):
    def setUp(self):
        self.workspace_root = "./test_governance_workspace"
        os.makedirs(self.workspace_root, exist_ok=True)
        
        # Create standard structure
        for folder in [
            "docs/brainstorming", "docs/plans", "docs/architecture-reviews", 
            "docs/blueprints", "docs/implementation", "docs/verification", 
            "docs/releases", "docs/reports", "docs/operations",
            ".agents/state", ".agents/config"
        ]:
            os.makedirs(os.path.join(self.workspace_root, folder), exist_ok=True)
            
        # Write temporary phase registry config
        self.registry_path = os.path.join(self.workspace_root, ".agents", "config", "phase_registry.json")
        import json
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump({
                "planning": {
                    "skill": "planning",
                    "agent": "planning-agent",
                    "next": "Gate1_PlanApproval",
                    "evidence": ["docs/plans/FEAT-123_plan.md"]
                }
            }, f)

    def tearDown(self):
        if os.path.exists(self.workspace_root):
            shutil.rmtree(self.workspace_root)

    def test_validate_artifact_path_success(self):
        # Valid planning path
        res = ArtifactGovernance.validate_artifact_path(
            "docs/plans/FEAT-123_plan.md", "planning", self.workspace_root
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["code"], "OK")

        # Valid blueprint path
        res = ArtifactGovernance.validate_artifact_path(
            "docs/blueprints/FEAT-123_blueprint.md", "blueprint", self.workspace_root
        )
        self.assertEqual(res["status"], "success")

    def test_validate_artifact_path_root_violation(self):
        # Markdown file at project root is forbidden
        res = ArtifactGovernance.validate_artifact_path(
            "FEAT-123_plan.md", "planning", self.workspace_root
        )
        self.assertEqual(res["status"], "failure")
        self.assertEqual(res["code"], "ARTIFACT_LOCATION_VIOLATION")

    def test_validate_artifact_path_folder_mismatch(self):
        # Storing planning artifact in brainstorming folder is forbidden
        res = ArtifactGovernance.validate_artifact_path(
            "docs/brainstorming/FEAT-123_plan.md", "planning", self.workspace_root
        )
        self.assertEqual(res["status"], "failure")
        self.assertEqual(res["code"], "ARTIFACT_LOCATION_VIOLATION")

    def test_validate_artifact_path_filename_convention(self):
        # Invalid planning filename format
        res = ArtifactGovernance.validate_artifact_path(
            "docs/plans/invalid_name.md", "planning", self.workspace_root
        )
        self.assertEqual(res["status"], "failure")
        self.assertEqual(res["code"], "FILENAME_CONVENTION_VIOLATION")

    def test_scan_root_violations(self):
        # Create a clean file and a violation file
        clean_file = os.path.join(self.workspace_root, "README.md")
        violation_file = os.path.join(self.workspace_root, "FEAT-123_report.md")
        
        with open(clean_file, "w") as f:
            f.write("Hello")
        with open(violation_file, "w") as f:
            f.write("Violation")
            
        violations = ArtifactGovernance.scan_root_violations(self.workspace_root)
        self.assertIn("FEAT-123_report.md", violations)
        self.assertNotIn("README.md", violations)

    def test_workflow_supervisor_blocking(self):
        supervisor = WorkflowSupervisor(
            workspace_root=self.workspace_root,
            registry_path=self.registry_path
        )
        # Force machine state to planning phase
        supervisor.state_machine.current_state = "Planning"
        
        # Test 1: Missing evidence file completely (violates path validation due to missing)
        state = supervisor.run_supervisor_step({"plan_file": "FEAT-123_plan.md"})
        self.assertEqual(state, "Planning")  # Should be blocked and stay in Planning
        
        # Test 2: Valid evidence path provided but file doesn't exist yet
        # If we provide a path that is in correct folder, let's see:
        # validate_artifact_path does not enforce file liveness if we only check path (unless missing_path check)
        # Let's create the valid file in correct folder
        valid_path = os.path.join(self.workspace_root, "docs/plans/FEAT-123_plan.md")
        with open(valid_path, "w") as f:
            f.write("PLAN APPROVED")
            
        # Run step with valid plan file
        state = supervisor.run_supervisor_step({"plan_file": "docs/plans/FEAT-123_plan.md"})
        self.assertEqual(state, "Gate1_PlanApproval")  # Advanced successfully!

if __name__ == "__main__":
    unittest.main()
