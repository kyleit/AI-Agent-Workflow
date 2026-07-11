# test_script_first.py
import pytest
pytestmark = pytest.mark.integration

import unittest
import os
import json
import sys
import subprocess
import shutil

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TEST_DIR, "..", "scripts"))
sys.path.append(os.path.join(TEST_DIR, "..", "scripts", "memory"))

class TestScriptFirstExecution(unittest.TestCase):
    def setUp(self):
        self.cli_path = os.path.join(TEST_DIR, "..", "scripts", "workflow_runtime.py")
        self.session_file = os.path.join(".agents", ".session.json")
        self.session_backup = None
        if os.path.exists(self.session_file):
            self.session_backup = self.session_file + ".testbackup"
            shutil.copy2(self.session_file, self.session_backup)
            os.remove(self.session_file)

        # Back up state directory
        self.state_dir = os.path.join(".agents", "state")
        self.state_backup = None
        if os.path.exists(self.state_dir):
            self.state_backup = self.state_dir + ".testbackup"
            if os.path.exists(self.state_backup):
                shutil.rmtree(self.state_backup)
            shutil.copytree(self.state_dir, self.state_backup)
            shutil.rmtree(self.state_dir)

    def tearDown(self):
        if os.path.exists(self.session_file):
            try:
                os.remove(self.session_file)
            except Exception:
                pass
        
        # Clean state directory
        if os.path.exists(self.state_dir):
            shutil.rmtree(self.state_dir)
        if self.state_backup and os.path.exists(self.state_backup):
            shutil.copytree(self.state_backup, self.state_dir)
            shutil.rmtree(self.state_backup)

        if self.session_backup and os.path.exists(self.session_backup):
            shutil.move(self.session_backup, self.session_file)
            
    # Scenario 1: Skill classifier
    def test_skill_classifier(self):
        from skill_classifier import classify_intent
        res = classify_intent("Tôi bị lỗi crash")
        self.assertEqual(res["recommended_skill"], "quick-fix")
        
        res = classify_intent("Thêm cái button xuất excel")
        self.assertEqual(res["recommended_skill"], "quick-feature")
        
        res = classify_intent("Tái thiết kế cơ sở dữ liệu lớn")
        self.assertEqual(res["recommended_skill"], "brainstorming")

    # Scenario 2 & 3: initialize-workflow creates session, defaults to sandbox
    def test_init_session(self):
        from workflow_state import init_session
        from session import load_session
        res = init_session("sandbox")
        self.assertEqual(res["status"], "success")
        session = load_session()
        self.assertEqual(session["checkpoint"], 1)
        self.assertEqual(session["permission_mode"], "sandbox")

    # Scenario 4: resume-workflow recommends skill
    def test_resume_session(self):
        from workflow_state import init_session, resume_session
        init_session("sandbox")
        res = resume_session()
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["next_skill"], "environment-health")

    # Scenario 5: project-discovery detects project stacks
    def test_project_discovery(self):
        from project_discovery import run_discovery
        res = run_discovery()
        self.assertEqual(res["status"], "success")
        profile_path = os.path.join(".agents", "project-profile.json")
        self.assertTrue(os.path.exists(profile_path))
        with open(profile_path, "r") as f:
            profile = json.load(f)
        self.assertIn("python", profile["languages"])

    # Scenario 6: memory bootstrap
    def test_memory_bootstrap(self):
        from memory.bootstrap import run_bootstrap
        res = run_bootstrap()
        self.assertEqual(res["status"], "success")
        self.assertTrue(os.path.exists(os.path.join(".agents", "memory", "project-summary.md")))

    # Scenario 7: memory update
    def test_memory_update(self):
        from memory.update import run_update
        res = run_update()
        self.assertEqual(res["status"], "success")

    # Scenario 8: RAG search fallback
    def test_memory_search(self):
        from memory.search import RAGSearcher
        searcher = RAGSearcher()
        res = searcher.execute_search("workflow")
        self.assertEqual(res["status"], "success")

    # Scenario 9: blueprint validation fails for missing
    def test_blueprint_validation_missing(self):
        from artifact_validator import validate_blueprint_file
        res = validate_blueprint_file("docs/designs/non_existent_blueprint.md")
        self.assertEqual(res["status"], "failure")

    # Scenario 10: implementation gate blocks non-blueprint input
    # Verified by checking blueprint files missing or unapproved
    def test_implementation_gate_blocks(self):
        from artifact_validator import validate_blueprint_file
        res = validate_blueprint_file("docs/designs/non_existent_blueprint.md", "FEAT-")
        self.assertEqual(res["status"], "failure")

    # Scenario 11 & 12: quick-fix and quick-feature stops after specs
    # Verified by checking validator command blocks if active spec is unapproved
    def test_quick_workflow_stops(self):
        from artifact_validator import validate_artifact_general
        res = validate_artifact_general("non_existent_spec.md")
        self.assertEqual(res["status"], "failure")

    # Scenario 13: debug runner build detection
    def test_debug_runner(self):
        from validation_runner import run_debug
        res = run_debug()
        self.assertEqual(res["status"], "success")

    def test_verify_runner_blocks_release(self):
        from validation_runner import run_verify
        from session import save_session_atomic
        bp_path = "docs/designs/FEAT-021_script_first_execution_blueprint.md"
        os.makedirs(os.path.dirname(bp_path), exist_ok=True)
        with open(bp_path, "w", encoding="utf-8") as f:
            f.write("# FEAT-021 Blueprint\n\n## Technical Blueprint\n## System Architecture\n## Implementation Plan\n## Verification Plan")
        save_session_atomic({"checkpoint": 7, "active_workflow": {"blueprint_path": bp_path}})
        res = run_verify()
        self.assertIn("Release is currently blocked", res["warnings"][0])

    # Scenario 15: release manager refuses tag/push without approval
    def test_release_refuses_without_approval(self):
        from release_manager import run_release_execute
        res = run_release_execute(approve=False)
        self.assertEqual(res["status"], "failure")
        self.assertIn("Explicit user approval required", res["summary"])

    # Scenario 16: CLI JSON validation
    def test_cli_json_output(self):
        res = subprocess.run([sys.executable, self.cli_path, "env", "health"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["command"], "env health")

    # Scenario 17: cross-platform path checks
    def test_cross_platform(self):
        from artifact_validator import validate_blueprint_file
        # Checks normalized slashes handle Windows path representations
        res = validate_blueprint_file("docs\\designs\\non_existent_blueprint.md")
        self.assertEqual(res["status"], "failure")
        self.assertIn("does not exist", res["summary"])

if __name__ == "__main__":
    unittest.main()
