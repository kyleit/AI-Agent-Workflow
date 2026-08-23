# test_runtime_validation.py
import pytest
pytestmark = pytest.mark.integration

import unittest
import os
import sys
import shutil
import json
import time
import subprocess

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from validation_runner import (
    detect_project_type,
    classify_log_error,
    is_port_open,
    run_smoke_test,
    run_debug,
    run_verify
)
from state_store import reset_state_store
from session import save_session_atomic

class TestRuntimeValidationPipeline(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "1"
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_validation_test"))
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
            
        # Create mock requirements.txt to satisfy project detection in test
        with open("requirements.txt", "w", encoding="utf-8") as f:
            f.write("pytest")
            
        # Create mock tests directory and dummy test file to satisfy pytest execution
        os.makedirs("tests", exist_ok=True)
        with open(os.path.join("tests", "test_dummy.py"), "w", encoding="utf-8") as f:
            f.write("def test_dummy():\n    assert True\n")

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

    def test_detect_project_type(self):
        # 1. Test Go detection
        go_dir = os.path.join(self.test_dir, "go_project")
        os.makedirs(go_dir, exist_ok=True)
        with open(os.path.join(go_dir, "go.mod"), "w", encoding="utf-8") as f:
            f.write("module test")
        self.assertEqual(detect_project_type(go_dir), "go")
        
        # 2. Test Python detection
        py_dir = os.path.join(self.test_dir, "py_project")
        os.makedirs(py_dir, exist_ok=True)
        with open(os.path.join(py_dir, "requirements.txt"), "w", encoding="utf-8") as f:
            f.write("pytest")
        self.assertEqual(detect_project_type(py_dir), "python")

    def test_classify_log_error(self):
        # Build Error
        self.assertEqual(classify_log_error("gofmt: build failed: syntax error"), "Build Error")
        # Dependency Error
        self.assertEqual(classify_log_error("ImportError: no required module provides package gorilla"), "Dependency Error")
        # Network Error
        self.assertEqual(classify_log_error("port binding failure: address already in use"), "Network Error")
        # Database Error
        self.assertEqual(classify_log_error("database is locked: OperationalError"), "Database Error")
        # Configuration Error
        self.assertEqual(classify_log_error("missing config or invalid yaml"), "Configuration Error")
        # Runtime Error
        self.assertEqual(classify_log_error("panic: runtime traceback exception"), "Runtime Error")
        # Unknown
        self.assertIsNone(classify_log_error("all steps completed successfully"))

    def test_wait_for_readiness_and_smoke_test(self):
        # Start a local python mock http server
        port = 9899
        proc = subprocess.Popen([sys.executable, "-m", "http.server", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait up to 5 seconds for port to open
        opened = False
        for _ in range(25):
            if is_port_open(port):
                opened = True
                break
            time.sleep(0.2)
            
        self.assertTrue(opened)
        
        # Check smoke test
        passed, msg = run_smoke_test(port)
        self.assertTrue(passed)
        self.assertTrue("Smoke test succeeded" in msg or "Smoke test responded with status" in msg)
        
        proc.terminate()
        proc.wait()

    def test_run_debug_execution_and_verify(self):
        save_session_atomic({
            "permission_mode": "sandbox",
            "work_item": {"id": "FEAT-115"}
        })
        
        # Since we are running in workspace root, python pytest detection will be activated
        # and we mock validation runner run_debug which should test correctly
        res = run_debug()
        self.assertEqual(res["status"], "success")
        self.assertIn("All validation pipeline steps PASSED.", res["summary"])
        
        # Test verify wrapper
        v_res = run_verify()
        self.assertEqual(v_res["status"], "success")
        self.assertIn("verification complete.", v_res["summary"])
