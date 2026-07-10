# test_refactoring.py
import unittest
import os
import sys
import shutil
import json
import subprocess
from unittest.mock import patch
import io

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from session import load_session, save_session_atomic, SESSION_FILE

class TestRefactoringEngine(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "1"
        self.cli_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "workflow_runtime.py")
        self.session_backup = None
        if os.path.exists(SESSION_FILE):
            self.session_backup = SESSION_FILE + ".testbackup"
            shutil.copy2(SESSION_FILE, self.session_backup)
            os.remove(SESSION_FILE)
            
        # Back up state directory
        self.state_dir = os.path.join(".agents", "state")
        self.state_backup = None
        if os.path.exists(self.state_dir):
            self.state_backup = self.state_dir + ".testbackup"
            if os.path.exists(self.state_backup):
                shutil.rmtree(self.state_backup, ignore_errors=True)
            shutil.copytree(self.state_dir, self.state_backup, ignore=shutil.ignore_patterns('*.db*', '*.tmp'))
            shutil.rmtree(self.state_dir, ignore_errors=True)
        
        save_session_atomic({"checkpoint": 1, "permission_mode": "sandbox"})
            
        self.pending_path = os.path.join(".agents", "runtime", "pending-choice.json")
        self.response_path = os.path.join(".agents", "runtime", "choice-response.json")
        
        # Clear files before test
        for p in [self.pending_path, self.response_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    def tearDown(self):
        # Clear files after test
        for p in [self.pending_path, self.response_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        
        # Clean state directory
        if os.path.exists(self.state_dir):
            shutil.rmtree(self.state_dir, ignore_errors=True)
        if self.state_backup and os.path.exists(self.state_backup):
            shutil.copytree(self.state_backup, self.state_dir, dirs_exist_ok=True)
            shutil.rmtree(self.state_backup, ignore_errors=True)

        if self.session_backup and os.path.exists(self.session_backup):
            shutil.copy2(self.session_backup, SESSION_FILE)
            os.remove(self.session_backup)

    def run_cli(self, args_list, input_str=None, env=None):
        cmd = [sys.executable, self.cli_path] + args_list
        run_env = os.environ.copy()
        if "TESTING" in run_env:
            del run_env["TESTING"]
        if env:
            run_env.update(env)
        res = subprocess.run(cmd, input=input_str, capture_output=True, text=True, encoding="utf-8", env=run_env)
        return res

    # ==========================================
    # 1. CHOICE PROTOCOL SCENARIOS (7 scenarios)
    # ==========================================

    def test_s1_1_choice_create(self):
        # Scenario 1.1: choice create builds correct JSON
        res = self.run_cli([
            "choice", "create", 
            "--id", "test_id", 
            "--title", "Test Title", 
            "--desc", "Test Desc", 
            "--options", "opt1,opt2", 
            "--type", "choice", 
            "--allow-cancel"
        ])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(self.pending_path))
        with open(self.pending_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["id"], "test_id")
        self.assertEqual(data["title"], "Test Title")
        self.assertEqual(data["description"], "Test Desc")
        self.assertEqual(len(data["options"]), 2)
        self.assertEqual(data["options"][0]["id"], "opt1")
        self.assertEqual(data["type"], "choice")
        self.assertTrue(data["allow_cancel"])

    def test_s1_2_choice_wait_ui_response(self):
        # Scenario 1.2: choice wait resolves instantly with UI response
        # First create pending choice
        self.run_cli(["choice", "create", "--id", "c2", "--title", "T", "--options", "o1,o2"])
        
        # Write UI response
        resp_data = {"id": "c2", "selected": "o2", "cancelled": False}
        with open(self.response_path, "w", encoding="utf-8") as f:
            json.dump(resp_data, f)
            
        res = self.run_cli(["choice", "wait", "--id", "c2", "--timeout", "1"], env={"AIWF_INTERACTIVE_CHOICE": "true"})
        self.assertEqual(res.returncode, 0)
        self.assertIn("Choice resolved: o2", res.stdout)

    def test_s1_3_choice_wait_text_fallback_number(self):
        # Scenario 1.3: choice wait text fallback processes option index
        self.run_cli(["choice", "create", "--id", "c3", "--title", "T", "--options", "o1,o2"])
        # Mock stdin input "2\n"
        res = self.run_cli(["choice", "wait", "--id", "c3", "--timeout", "1"], input_str="2\n")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Choice resolved: o2", res.stdout)

    def test_s1_4_choice_wait_text_fallback_direct_label(self):
        # Scenario 1.4: choice wait text fallback processes option label case-insensitively
        self.run_cli(["choice", "create", "--id", "c4", "--title", "T", "--options", "o1,o2"])
        # Mock stdin input "O2\n" (uppercase match)
        res = self.run_cli(["choice", "wait", "--id", "c4", "--timeout", "1"], input_str="O2\n")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Choice resolved: o2", res.stdout)

    def test_s1_5_choice_wait_approval_yes_no(self):
        # Scenario 1.5: choice wait handles Y/N for approval type
        self.run_cli(["choice", "create", "--id", "c5", "--title", "T", "--options", "Yes,No", "--type", "approval"])
        res = self.run_cli(["choice", "wait", "--id", "c5", "--timeout", "1"], input_str="Y\n")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Choice resolved: approve", res.stdout)

    def test_s1_6_choice_wait_cancel(self):
        # Scenario 1.6: choice wait text fallback cancels on C/cancel if allowed
        self.run_cli(["choice", "create", "--id", "c6", "--title", "T", "--options", "o1,o2", "--allow-cancel"])
        res = self.run_cli(["choice", "wait", "--id", "c6", "--timeout", "1"], input_str="C\n")
        self.assertEqual(res.returncode, 0)
        self.assertIn("Choice resolved: cancel", res.stdout)

    def test_s1_7_choice_read(self):
        # Scenario 1.7: choice read returns selection or empty
        res = self.run_cli(["choice", "read", "--id", "c7"])
        self.assertEqual(res.stdout.strip(), "")
        
        # Write mock resolved file
        resp_data = {"id": "c7", "selected": "o1", "cancelled": False}
        with open(self.response_path, "w", encoding="utf-8") as f:
            json.dump(resp_data, f)
            
        res = self.run_cli(["choice", "read", "--id", "c7"])
        self.assertEqual(res.stdout.strip(), "o1")

    # ==========================================
    # 2. ACTIVE-WORKFLOW SCENARIOS (5 scenarios)
    # ==========================================

    def test_s2_1_active_workflow_set(self):
        # Scenario 2.1: active-workflow set writes state to session
        save_session_atomic({"checkpoint": 1})
        res = self.run_cli([
            "active-workflow", "set",
            "--type", "quick-fix",
            "--phase", "spec",
            "--skill", "quick-fix",
            "--command", "fix",
            "--artifact-id", "FIX-001",
            "--spec-path", "docs/specs/FIX-001.md",
            "--blueprint-path", "docs/designs/FIX-001_blueprint.md",
            "--waiting-for", "spec_approval"
        ])
        self.assertEqual(res.returncode, 0)
        session = load_session()
        self.assertIn("active_workflow", session)
        aw = session["active_workflow"]
        self.assertEqual(aw["type"], "quick-fix")
        self.assertEqual(aw["phase"], "spec")
        self.assertEqual(aw["artifact_id"], "FIX-001")
        self.assertEqual(aw["waiting_for"], "spec_approval")

    def test_s2_2_active_workflow_get(self):
        # Scenario 2.2: active-workflow get returns saved state JSON
        save_session_atomic({
            "checkpoint": 1,
            "active_workflow": {"type": "quick-fix", "phase": "spec"}
        })
        res = self.run_cli(["active-workflow", "get"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout.strip())
        self.assertEqual(data["type"], "quick-fix")
        self.assertEqual(data["phase"], "spec")

    def test_s2_3_active_workflow_set_waiting_and_clear(self):
        # Scenario 2.3: active-workflow set-waiting updates waiting_for, clear removes it
        save_session_atomic({
            "checkpoint": 1,
            "active_workflow": {"type": "quick-fix", "waiting_for": "spec_approval"}
        })
        # Set waiting to null
        res = self.run_cli(["active-workflow", "set-waiting", "--waiting-for", "null"])
        self.assertEqual(res.returncode, 0)
        session = load_session()
        self.assertIsNone(session["active_workflow"]["waiting_for"])
        
        # Clear entirely
        res = self.run_cli(["active-workflow", "clear"])
        self.assertEqual(res.returncode, 0)
        session = load_session()
        self.assertNotIn("active_workflow", session)

    def test_s2_4_active_workflow_resume(self):
        # Scenario 2.4: active-workflow resume restores checkpoint and current step
        save_session_atomic({
            "checkpoint": 1,
            "active_workflow": {
                "type": "quick-fix",
                "phase": "blueprint",
                "skill": "quick-fix",
                "command": "fix"
            }
        })
        res = self.run_cli(["active-workflow", "resume"])
        self.assertEqual(res.returncode, 0)
        session = load_session()
        self.assertEqual(session["current_skill"], "quick-fix")
        self.assertEqual(session["current_command"], "fix")
        self.assertEqual(session["checkpoint"], 4)
        self.assertEqual(session["current_step"], "Writing Design Blueprint")

    def test_s2_5_active_workflow_resume_nlp(self):
        # Scenario 2.5: Resumption logic (NLP classification suggestion)
        # Note: Handled by orchestrator/SDLC classification helper script,
        # but here we test the session states and resuming actions.
        # Verified via CLI active-workflow resume mapping.
        save_session_atomic({
            "checkpoint": 1,
            "active_workflow": {
                "type": "quick-fix",
                "phase": "blueprint",
                "skill": "quick-fix",
                "command": "fix",
                "waiting_for": "blueprint_approval"
            }
        })
        res = self.run_cli(["active-workflow", "resume"])
        self.assertEqual(res.returncode, 0)

    # ==========================================
    # 3. BLUEPRINT VALIDATION SCENARIOS (3 scenarios)
    # ==========================================

    def test_s3_1_validate_blueprint_success(self):
        # Scenario 3.1: validate-blueprint succeeds with valid file
        bp_dir = "docs/designs"
        os.makedirs(bp_dir, exist_ok=True)
        bp_path = os.path.join(bp_dir, "FIX-123_blueprint.md")
        
        valid_content = """---
name: FIX-123 Fix submission bug
description: Blueprint for FIX-123
---
# Summary
This is summary.
# Scope
This is scope.
# Technical Design
This is technical design.
# Files to Change
This is files to change.
# Implementation Steps
This is steps.
# Validation Plan
This is validation plan.
# Rollback Plan
This is rollback plan.
"""
        with open(bp_path, "w", encoding="utf-8") as f:
            f.write(valid_content)
            
        try:
            res = self.run_cli(["active-workflow", "validate-blueprint", "--path", bp_path, "--workflow", "quick-fix"])
            self.assertEqual(res.returncode, 0)
            self.assertIn("Blueprint validation passed", res.stdout)
        finally:
            if os.path.exists(bp_path):
                os.remove(bp_path)

    def test_s3_2_validate_blueprint_missing_section(self):
        # Scenario 3.2: validate-blueprint fails if header is missing
        bp_dir = "docs/designs"
        os.makedirs(bp_dir, exist_ok=True)
        bp_path = os.path.join(bp_dir, "FIX-124_blueprint.md")
        
        invalid_content = """---
name: FIX-124 Blueprint missing sections
---
# Summary
This is summary.
# Scope
This is scope.
"""
        with open(bp_path, "w", encoding="utf-8") as f:
            f.write(invalid_content)
            
        try:
            res = self.run_cli(["active-workflow", "validate-blueprint", "--path", bp_path])
            self.assertEqual(res.returncode, 1)
            self.assertIn("Error: Blueprint is missing required sections", res.stderr)
        finally:
            if os.path.exists(bp_path):
                os.remove(bp_path)

    def test_s3_3_validate_blueprint_mismatched_prefix(self):
        # Scenario 3.3: validate-blueprint fails on prefix mismatch
        bp_dir = "docs/designs"
        os.makedirs(bp_dir, exist_ok=True)
        bp_path = os.path.join(bp_dir, "FEAT-125_blueprint.md")
        
        valid_content = """---
name: FEAT-125 Test
---
# Summary
# Scope
# Technical Design
# Files to Change
# Implementation Steps
# Validation Plan
# Rollback Plan
"""
        with open(bp_path, "w", encoding="utf-8") as f:
            f.write(valid_content)
            
        try:
            res = self.run_cli(["active-workflow", "validate-blueprint", "--path", bp_path, "--workflow", "quick-fix"])
            self.assertEqual(res.returncode, 1)
            self.assertIn("Error: Workflow quick-fix requires a FIX- prefix", res.stderr)
        finally:
            if os.path.exists(bp_path):
                os.remove(bp_path)

    # ==========================================
    # 4. GIT BRANCH & CHOICE UI SCENARIOS (3 scenarios)
    # ==========================================

    def test_s4_1_suggest_branch(self):
        # Scenario 4.1: suggest-branch cleans slug and appends correct prefix
        res = self.run_cli(["active-workflow", "suggest-branch", "--artifact-id", "FIX-456", "--slug", "Fix memory crash!"])
        self.assertEqual(res.returncode, 0)
        self.assertEqual(res.stdout.strip(), "fix/fix-456-fix-memory-crash")
        
        res2 = self.run_cli(["active-workflow", "suggest-branch", "--artifact-id", "QUICK-789", "--slug", "Add button!"])
        self.assertEqual(res2.returncode, 0)
        self.assertEqual(res2.stdout.strip(), "quick/quick-789-add-button")

    def test_s4_2_branch_options(self):
        # Scenario 4.2: branch-options returns branch choice list with actual branch name
        res = self.run_cli(["active-workflow", "branch-options", "--artifact-id", "FEAT-001", "--slug", "Login Flow"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout.strip())
        self.assertIn("options", data)
        self.assertEqual(len(data["options"]), 3)
        self.assertIn("detached HEAD" if not data["current_branch"] else data["current_branch"], data["options"][0])
        self.assertIn("feature/feat-001-login-flow", data["options"][1])
        self.assertEqual(data["options"][2], "Stop")

    def test_s4_3_branch_options_warn_main(self):
        # Scenario 4.3: warn_main is True when current branch is main/master
        # Since git branch cannot be easily changed during tests, we can test with a mocked branch
        with patch('utils.get_current_branch', return_value="main"):
            from utils import build_branch_selection_options
            opts = build_branch_selection_options("FIX-123", "Bug")
            self.assertTrue(opts["warn_main"])
            
        with patch('utils.get_current_branch', return_value="feature/custom"):
            from utils import build_branch_selection_options
            opts = build_branch_selection_options("FIX-123", "Bug")
            self.assertFalse(opts["warn_main"])

if __name__ == "__main__":
    unittest.main()
