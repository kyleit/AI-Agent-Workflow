# test_targeted_validation.py
import pytest
pytestmark = pytest.mark.integration

import unittest
import os
import sys
import shutil
import json
from unittest.mock import patch, MagicMock

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from validation_runner import run_pipeline
from session import save_session_atomic
from state_store import reset_state_store

class TestTargetedValidation(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "1"
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_targeted_test"))
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Override state root
        self.original_state_root = os.environ.get("AIWF_STATE_ROOT")
        os.environ["AIWF_STATE_ROOT"] = "."
        reset_state_store(None)

        # Mock context.json
        context_data = {
            "project_id": "test-project",
            "workspace_path": ".",
            "git": {"is_git_repository": False}
        }
        with open("context.json", "w", encoding="utf-8") as f:
            json.dump(context_data, f)

        # Create dummy directory structure
        os.makedirs("docs/designs", exist_ok=True)
        os.makedirs("skills/workflow-runtime/tests/smoke", exist_ok=True)
        os.makedirs("skills/workflow-runtime/tests/unit", exist_ok=True)
        os.makedirs("skills/workflow-runtime/tests/integration", exist_ok=True)
        
        # Create dummy test files
        self.smoke_test_path = "skills/workflow-runtime/tests/smoke/test_smoke.py"
        with open(self.smoke_test_path, "w", encoding="utf-8") as f:
            f.write("# smoke test\n")
            
        self.unit_test_path = "skills/workflow-runtime/tests/unit/test_permissions.py"
        with open(self.unit_test_path, "w", encoding="utf-8") as f:
            f.write("# permissions unit test\n")
            
        self.blueprint_test_path = "skills/workflow-runtime/tests/integration/test_targeted_validation.py"
        with open(self.blueprint_test_path, "w", encoding="utf-8") as f:
            f.write("# targeted validation integration test\n")

        self.knowledge_test_path = "skills/knowledge-runtime/tests/unit/test_runtime_api.py"
        os.makedirs(os.path.dirname(self.knowledge_test_path), exist_ok=True)
        with open(self.knowledge_test_path, "w", encoding="utf-8") as f:
            f.write("# knowledge test\n")

        # Mock blueprint JSON
        blueprint_data = {
            "tests": [
                {
                    "requirement_id": "REQ-405A-01",
                    "target_file": "skills/workflow-runtime/tests/integration/test_targeted_validation.py"
                }
            ]
        }
        with open("docs/designs/FIX-405A_targeted_workflow_runtime_validation_blueprint.json", "w", encoding="utf-8") as f:
            json.dump(blueprint_data, f)

    def tearDown(self):
        os.chdir(self.original_cwd)
        if self.original_state_root is not None:
            os.environ["AIWF_STATE_ROOT"] = self.original_state_root
        else:
            os.environ.pop("AIWF_STATE_ROOT", None)
            
        reset_state_store(None)
        
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception:
                pass
                
        os.environ.pop("AIWF_VALIDATION_TIER", None)

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("tia_engine.TestImpactResolver.get_git_changed_files")
    @patch("tia_engine.TestImpactResolver.resolve_affected_tests")
    def test_implementation_tier(self, mock_resolve_affected, mock_get_changed, mock_popen, mock_run):
        mock_get_changed.return_value = ["sources/db.py"]
        mock_resolve_affected.return_value = ["skills/workflow-runtime/tests/unit/test_permissions.py"]
        
        # Save session matching the tier
        save_session_atomic({
            "current_skill": "blueprint-to-implementation",
            "work_item": {"id": "FIX-405A"}
        })
        
        # Mock Popen for mock HTTP server startup check
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        
        # Run validation runner
        with patch("validation_runner.is_port_open", return_value=True), \
             patch("validation_runner.run_smoke_test", return_value=(True, "Success")):
            success, summary, warnings = run_pipeline("python", ".")
            
        self.assertTrue(success)
        
        # Assert pytest run only targeted + blueprint tests
        pytest_call = mock_run.call_args_list[0]
        cmd_args = pytest_call[0][0]
        self.assertEqual(cmd_args[0], "pytest")
        self.assertIn("skills/workflow-runtime/tests/unit/test_permissions.py", cmd_args)
        self.assertIn("skills/workflow-runtime/tests/integration/test_targeted_validation.py", cmd_args)
        # Ensure it didn't run all tests (like smoke test unless specified)
        self.assertNotIn("skills/workflow-runtime/tests/smoke/test_smoke.py", cmd_args)

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("tia_engine.TestImpactResolver.get_git_changed_files")
    @patch("tia_engine.TestImpactResolver.resolve_affected_tests")
    def test_implementation_to_debug_tier(self, mock_resolve_affected, mock_get_changed, mock_popen, mock_run):
        mock_get_changed.return_value = ["skills/knowledge-runtime/scripts/api.py"]
        mock_resolve_affected.return_value = ["skills/knowledge-runtime/tests/unit/test_runtime_api.py"]
        
        # Save session matching the tier
        save_session_atomic({
            "current_skill": "implementation-to-debug",
            "work_item": {"id": "FIX-405A"}
        })
        
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        
        with patch("validation_runner.is_port_open", return_value=True), \
             patch("validation_runner.run_smoke_test", return_value=(True, "Success")):
            success, summary, warnings = run_pipeline("python", ".")
            
        self.assertTrue(success)
        
        pytest_call = mock_run.call_args_list[0]
        cmd_args = pytest_call[0][0]
        self.assertEqual(cmd_args[0], "pytest")
        self.assertIn("skills/knowledge-runtime/tests/unit/test_runtime_api.py", cmd_args)
        self.assertIn("skills/workflow-runtime/tests/smoke/test_smoke.py", cmd_args)
        # implementation-to-debug should NOT include blueprint-listed tests unless affected/module
        self.assertNotIn("skills/workflow-runtime/tests/integration/test_targeted_validation.py", cmd_args)

    @patch("subprocess.run")
    @patch("subprocess.Popen")
    @patch("tia_engine.TestImpactResolver.get_git_changed_files")
    @patch("tia_engine.TestImpactResolver.resolve_affected_tests")
    def test_debug_to_verify_tier(self, mock_resolve_affected, mock_get_changed, mock_popen, mock_run):
        mock_get_changed.return_value = ["sources/db.py"]
        mock_resolve_affected.return_value = ["skills/workflow-runtime/tests/unit/test_permissions.py"]
        
        # Save session matching the tier
        save_session_atomic({
            "current_skill": "debug-to-verify",
            "work_item": {"id": "FIX-405A"}
        })
        
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc
        
        with patch("validation_runner.is_port_open", return_value=True), \
             patch("validation_runner.run_smoke_test", return_value=(True, "Success")):
            success, summary, warnings = run_pipeline("python", ".")
            
        self.assertTrue(success)
        
        pytest_call = mock_run.call_args_list[0]
        cmd_args = pytest_call[0][0]
        self.assertEqual(cmd_args[0], "pytest")
        self.assertIn("skills/workflow-runtime/tests/unit/test_permissions.py", cmd_args)
        self.assertIn("skills/workflow-runtime/tests/integration/test_targeted_validation.py", cmd_args)
        self.assertNotIn("skills/workflow-runtime/tests/smoke/test_smoke.py", cmd_args)

    def test_drift_verification(self):
        # Locate project root (which is self.original_cwd)
        project_root = self.original_cwd
        skills_dir = os.path.join(project_root, "skills")
        agents_skills_dir = os.path.join(project_root, ".agents", "skills")
        
        # List of files we expect mirror parity for
        files_to_check = [
            "workflow-runtime/scripts/validation_runner.py",
            "blueprint-to-implementation/SKILL.md",
            "implementation-to-debug/SKILL.md"
        ]
        
        for rel_path in files_to_check:
            original_file = os.path.join(skills_dir, rel_path)
            mirror_file = os.path.join(agents_skills_dir, rel_path)
            
            self.assertTrue(os.path.exists(original_file), f"Original file {original_file} does not exist")
            self.assertTrue(os.path.exists(mirror_file), f"Mirror file {mirror_file} does not exist")
            
            with open(original_file, "r", encoding="utf-8") as f:
                original_content = f.read()
            with open(mirror_file, "r", encoding="utf-8") as f:
                mirror_content = f.read()
                
            self.assertEqual(original_content, mirror_content, f"Content mismatch between {original_file} and {mirror_file}")
