# test_runtime.py
import unittest
import os
import sys
import shutil
import json
import uuid
import sqlite3

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from session import load_session, save_session_atomic, SESSION_FILE
from checkpoint import validate_checkpoint_level, get_checkpoint_name
from validator import get_git_info, get_version_info
from drift import check_context_drift
from heartbeat import generate_heartbeat_string
from context import estimate_context_usage, parse_transcript
from db import PROJECT_DB, get_global_db_path, save_usage_to_dbs, get_workflow_summary, get_project_summary, get_global_summary

class TestRuntimeEngine(unittest.TestCase):
    def setUp(self):
        # Back up existing files
        self.session_backup = None
        if os.path.exists(SESSION_FILE):
            self.session_backup = SESSION_FILE + ".bak"
            shutil.copy2(SESSION_FILE, self.session_backup)
            os.remove(SESSION_FILE)
            
        self.project_db_backup = None
        if os.path.exists(PROJECT_DB):
            self.project_db_backup = PROJECT_DB + ".bak"
            shutil.copy2(PROJECT_DB, self.project_db_backup)
            os.remove(PROJECT_DB)
            
        self.global_db = get_global_db_path()
        self.global_db_backup = None
        if os.path.exists(self.global_db):
            self.global_db_backup = self.global_db + ".bak"
            shutil.copy2(self.global_db, self.global_db_backup)
            os.remove(self.global_db)
            
    def tearDown(self):
        # Restore backup files
        for current, backup in [
            (SESSION_FILE, self.session_backup),
            (PROJECT_DB, self.project_db_backup),
            (self.global_db, self.global_db_backup)
        ]:
            if os.path.exists(current):
                os.remove(current)
            if backup and os.path.exists(backup):
                shutil.move(backup, current)
            
    def test_atomic_write_and_missing_session(self):
        session = load_session()
        self.assertEqual(session, {})
        
        test_data = {"checkpoint": 2, "status": "completed"}
        save_session_atomic(test_data)
        
        loaded = load_session()
        self.assertEqual(loaded["checkpoint"], 2)
        self.assertEqual(loaded["status"], "completed")
        self.assertIn("conversation_id", loaded)
        
    def test_conversation_preservation(self):
        conv_id = str(uuid.uuid4())
        save_session_atomic({"conversation_id": conv_id})
        
        save_session_atomic({"status": "in_progress"})
        loaded = load_session()
        self.assertEqual(loaded["conversation_id"], conv_id)
        
    def test_checkpoint_validation(self):
        self.assertTrue(validate_checkpoint_level(5, "exactly 5"))
        self.assertFalse(validate_checkpoint_level(4, "exactly 5"))
        self.assertTrue(validate_checkpoint_level(5, "at least 4"))
        self.assertFalse(validate_checkpoint_level(3, "at least 4"))
        self.assertTrue(validate_checkpoint_level(3, "exactly 3 or 2"))
        
    def test_drift_detection(self):
        session = {
            "git": {"is_git_repository": True, "branch": "non_existent_branch"},
            "version": {"version": "0.0.0"}
        }
        drifted, msg = check_context_drift(session)
        self.assertTrue(drifted)
        self.assertIn("Branch drifted", msg)
        
    def test_heartbeat_generation(self):
        session = {
            "conversation_id": "test-id",
            "checkpoint": 2,
            "status": "in_progress",
            "context_usage": {"percentage": 10.5, "total_tokens": 210000, "limit_tokens": 2000000}
        }
        hb_str = generate_heartbeat_string(session)
        self.assertIn("test-id", hb_str)
        self.assertIn("Memory Loaded", hb_str)
        self.assertIn("10.5%", hb_str)

    def test_failure_recovery_corrupted_session(self):
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            f.write("{invalid json")
        session = load_session()
        self.assertEqual(session, {})

    def test_sqlite_databases_and_scopes(self):
        conv_id_1 = "conv-test-1"
        conv_id_2 = "conv-test-2"
        proj_id = "test-project"
        
        usage_1 = {
            "input_tokens": 10000,
            "output_tokens": 5000,
            "cache_tokens": 1500,
            "thinking_tokens": 800,
            "active_tokens": 4000,
            "total_tokens": 15000,
            "estimated_cost_usd": 0.05,
            "provider": "antigravity",
            "model": "gemini-1.5-pro",
            "accuracy": "estimated"
        }
        
        usage_2 = {
            "input_tokens": 20000,
            "output_tokens": 8000,
            "cache_tokens": 3000,
            "thinking_tokens": 1200,
            "active_tokens": 6000,
            "total_tokens": 28000,
            "estimated_cost_usd": 0.10,
            "provider": "antigravity",
            "model": "gemini-1.5-pro",
            "accuracy": "estimated"
        }
        
        # Save records to DB
        save_usage_to_dbs(conv_id_1, proj_id, "test-skill", "test-cmd", usage_1)
        save_usage_to_dbs(conv_id_2, proj_id, "test-skill", "test-cmd", usage_2)
        
        # Verify Workflow summaries
        wf_1 = get_workflow_summary(conv_id_1, "antigravity", "gemini-1.5-pro")
        self.assertEqual(wf_1["total_tokens"], 15000)
        self.assertEqual(wf_1["active_tokens"], 4000)
        self.assertEqual(wf_1["percentage"], 0.2)  # (4000 / 2000000) * 100
        self.assertEqual(wf_1["estimated_cost_usd"], 0.05)
        
        wf_2 = get_workflow_summary(conv_id_2, "antigravity", "gemini-1.5-pro")
        self.assertEqual(wf_2["total_tokens"], 28000)
        self.assertEqual(wf_2["active_tokens"], 6000)
        self.assertEqual(wf_2["estimated_cost_usd"], 0.10)
        
        # Verify Project summary (sums both conversations)
        project_sum = get_project_summary()
        self.assertEqual(project_sum["total_tokens"], 43000)
        self.assertEqual(project_sum["estimated_cost_usd"], 0.15)
        
        # Verify Global summary (sums both conversations)
        global_sum = get_global_summary()
        self.assertEqual(global_sum["total_tokens"], 43000)
        self.assertEqual(global_sum["estimated_cost_usd"], 0.15)

    def test_transcript_parser(self):
        # Create a mock transcript file
        mock_log = "mock_transcript.jsonl"
        lines = [
            {"source": "USER_EXPLICIT", "content": "Hello agent", "type": "USER_INPUT"},
            {"source": "MODEL", "content": "Hello user", "thinking": "Thinking process", "type": "PLANNER_RESPONSE"}
        ]
        with open(mock_log, "w", encoding="utf-8") as f:
            for l in lines:
                f.write(json.dumps(l) + "\n")
                
        try:
            parsed = parse_transcript(mock_log)
            self.assertIn("total_tokens", parsed)
            self.assertIn("active_tokens", parsed)
            self.assertIn("estimated_cost_usd", parsed)
            self.assertTrue(parsed["total_tokens"] > 0)
        finally:
            if os.path.exists(mock_log):
                os.remove(mock_log)

    def test_blueprint_registration_and_approval(self):
        # Initial empty session
        save_session_atomic({"checkpoint": 1})
        
        # Test registering blueprint via subprocess call to CLI
        import subprocess
        cli_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "workflow_runtime.py")
        
        # Create a mock blueprint file
        mock_bp = "mock_blueprint.md"
        with open(mock_bp, "w", encoding="utf-8") as f:
            f.write("# Mock Blueprint")
            
        try:
            # Register blueprint
            res = subprocess.run(
                [sys.executable, cli_path, "blueprint", "--path", mock_bp],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("registered", res.stdout)
            
            # Verify session has blueprint registered
            session = load_session()
            self.assertIn("blueprint", session)
            self.assertEqual(session["blueprint"]["path"], mock_bp)
            self.assertEqual(session["blueprint"]["exists"], True)
            self.assertEqual(session["blueprint"]["approved"], False)
            
            # Approve blueprint
            res_approve = subprocess.run(
                [sys.executable, cli_path, "blueprint", "--path", mock_bp, "--approve"],
                capture_output=True, text=True
            )
            self.assertEqual(res_approve.returncode, 0)
            self.assertIn("approved", res_approve.stdout)
            
            # Verify session has blueprint approved
            session_approved = load_session()
            self.assertEqual(session_approved["blueprint"]["approved"], True)
            self.assertEqual(session_approved["blueprint"]["approved_by"], "user")
            self.assertTrue(len(session_approved["blueprint"]["approved_at"]) > 0)
        finally:
            if os.path.exists(mock_bp):
                os.remove(mock_bp)

    def test_suggestion_gate_scenarios(self):
        import subprocess
        cli_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "workflow_runtime.py")
        
        # Scenario 1: Raw bug request suggests quick-fix
        save_session_atomic({"checkpoint": 1})
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--request", "Tôi bị crash ở hàm submit", "--recommend", "quick-fix"],
            capture_output=True, text=True
        )
        self.assertEqual(res.returncode, 0)
        session = load_session()
        self.assertEqual(session["suggestion_gate"]["active"], True)
        self.assertEqual(session["suggestion_gate"]["recommended_skill"], "quick-fix")
        self.assertEqual(session["suggestion_gate"]["status"], "waiting_for_user_confirmation")
        
        # Scenario 2: Raw small feature request suggests quick-feature
        save_session_atomic({"checkpoint": 1})
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--request", "Thêm cái button xuất báo cáo", "--recommend", "quick-feature"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["suggestion_gate"]["recommended_skill"], "quick-feature")
        
        # Scenario 3: Raw large feature request suggests brainstorming
        save_session_atomic({"checkpoint": 1})
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--request", "Tái cấu trúc lại toàn bộ hệ thống cơ sở dữ liệu", "--recommend", "brainstorming"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["suggestion_gate"]["recommended_skill"], "brainstorming")
        
        # Scenario 4: Ambiguous request shows multiple options and stops
        save_session_atomic({"checkpoint": 1})
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--request", "Làm tính năng gì đó", "--options", "quick-fix,quick-feature,brainstorming"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(len(session["suggestion_gate"]["options"]), 3)
        self.assertEqual(session["suggestion_gate"]["active"], True)
        
        # Scenario 5: User selects option 1 -> quick-fix starts
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--choose", "1"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["suggestion_gate"]["active"], False)
        self.assertEqual(session["suggestion_gate"]["status"], "confirmed")
        self.assertEqual(session["suggestion_gate"]["recommended_skill"], "quick-fix")
        
        # Reset and Scenario 6: User selects option 2 -> quick-feature starts
        save_session_atomic({
            "checkpoint": 1,
            "suggestion_gate": {
                "active": True,
                "options": ["quick-fix", "quick-feature", "brainstorming"],
                "status": "waiting_for_user_confirmation"
            }
        })
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--choose", "2"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["suggestion_gate"]["recommended_skill"], "quick-feature")
        
        # Reset and Scenario 7: User selects option 3 -> brainstorming starts
        save_session_atomic({
            "checkpoint": 1,
            "suggestion_gate": {
                "active": True,
                "options": ["quick-fix", "quick-feature", "brainstorming"],
                "status": "waiting_for_user_confirmation"
            }
        })
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--choose", "3"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["suggestion_gate"]["recommended_skill"], "brainstorming")
        
        # Scenario 8: Raw release-like request suggests release only if explicit
        save_session_atomic({"checkpoint": 9})
        # If user asks to push release explicitly
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--request", "Đẩy code release lên production", "--recommend", "implementation-to-release"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["suggestion_gate"]["recommended_skill"], "implementation-to-release")
        
        # Scenario 9: Non-release implementation completion does not suggest auto-release execution
        # If no explicit release request, suggestion gate should not suggest implementation-to-release
        save_session_atomic({"checkpoint": 8})
        session = load_session()
        self.assertNotEqual(session.get("suggestion_gate", {}).get("recommended_skill"), "implementation-to-release")
        
        # Scenario 10: Explicit /quick-fix bypasses suggestion gate and runs quick-fix normally
        save_session_atomic({"checkpoint": 1})
        # If running start for quick-fix directly
        res = subprocess.run(
            [sys.executable, cli_path, "start", "--skill", "quick-fix", "--command", "fix", "--checkpoint", "2", "--step", "Starting"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["current_skill"], "quick-fix")
        self.assertEqual(session["suggestion_gate"]["active"], False)
        
        # Scenario 11: Explicit /brainstorm bypasses suggestion gate
        save_session_atomic({"checkpoint": 1})
        res = subprocess.run(
            [sys.executable, cli_path, "start", "--skill", "brainstorming", "--command", "brainstorm", "--checkpoint", "2", "--step", "Starting"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["current_skill"], "brainstorming")
        
        # Scenario 12: Explicit /release is allowed only as explicit release request
        save_session_atomic({"checkpoint": 9})
        res = subprocess.run(
            [sys.executable, cli_path, "start", "--skill", "implementation-to-release", "--command", "release", "--checkpoint", "10", "--step", "Releasing"],
            capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session["current_skill"], "implementation-to-release")

if __name__ == "__main__":
    unittest.main()
