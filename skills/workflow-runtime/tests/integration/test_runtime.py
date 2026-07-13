# test_runtime.py
import pytest
pytestmark = pytest.mark.integration

import unittest
import os
import sys
import shutil
import json
import uuid
import sqlite3
import subprocess

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".agents", "skills", "workflow-runtime", "scripts")))

from session import load_session, save_session_atomic, SESSION_FILE
from checkpoint import validate_checkpoint_level, get_checkpoint_name
from validator import get_git_info, get_version_info
from drift import check_context_drift
from heartbeat import generate_heartbeat_string
from context import estimate_context_usage, parse_transcript
from db import PROJECT_DB, get_global_db_path, save_usage_to_dbs, get_workflow_summary, get_project_summary, get_global_summary
import db
import analytics_engine

class TestRuntimeEngine(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "1"
        
        # Isolate databases to a temp directory
        self.test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_test_db"))
        os.makedirs(self.test_dir, exist_ok=True)
        self.original_project_db = db.PROJECT_DB
        db.PROJECT_DB = os.path.join(self.test_dir, "test_project_runtime.db")
        self.original_get_global_db = db.get_global_db_path
        db.get_global_db_path = lambda: os.path.join(self.test_dir, "test_global_runtime.db")
        
        # Isolate lock and lease files for testing
        self.lock_file = os.path.join(".agents", "runtime", "workflow.lock")
        self.lease_file = os.path.join(".agents", "runtime", "workflow-lease.json")
        self.lock_backup = None
        if os.path.exists(self.lock_file):
            self.lock_backup = self.lock_file + ".testbackup"
            try:
                shutil.copy2(self.lock_file, self.lock_backup)
                os.remove(self.lock_file)
            except Exception:
                pass
        self.lease_backup = None
        if os.path.exists(self.lease_file):
            self.lease_backup = self.lease_file + ".testbackup"
            try:
                shutil.copy2(self.lease_file, self.lease_backup)
                os.remove(self.lease_file)
            except Exception:
                pass
        
        # Back up existing files to temporary testbackup names
        self.session_backup = None
        if os.path.exists(SESSION_FILE):
            self.session_backup = SESSION_FILE + ".testbackup"
            try:
                shutil.copy2(SESSION_FILE, self.session_backup)
                os.remove(SESSION_FILE)
            except Exception:
                pass
            
        # Back up state directory
        self.state_dir = os.path.join(".agents", "state")
        self.state_backup = None
        if os.path.exists(self.state_dir):
            self.state_backup = self.state_dir + ".testbackup"
            try:
                if os.path.exists(self.state_backup):
                    shutil.rmtree(self.state_backup, ignore_errors=True)
                shutil.copytree(self.state_dir, self.state_backup, ignore=shutil.ignore_patterns('*.db*', '*.tmp'))
                shutil.rmtree(self.state_dir, ignore_errors=True)
            except Exception:
                pass

        # Clean session.json.bak if it exists
        bak_file = SESSION_FILE + ".bak"
        if os.path.exists(bak_file):
            try:
                os.remove(bak_file)
            except Exception:
                pass
            
    def tearDown(self):
        # Restore DB paths
        db.PROJECT_DB = self.original_project_db
        db.get_global_db_path = self.original_get_global_db
        
        # Clean up temp test directory
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except Exception:
                pass
                
        # Clean lock and lease files and restore backups if any
        for f, backup in [(self.lock_file, self.lock_backup), (self.lease_file, self.lease_backup)]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
            if backup and os.path.exists(backup):
                try:
                    shutil.copy2(backup, f)
                    os.remove(backup)
                except Exception:
                    pass

        # Clean any generated session.json.bak
        bak_file = SESSION_FILE + ".bak"
        if os.path.exists(bak_file):
            try:
                os.remove(bak_file)
            except Exception:
                pass

        # Clean state directory
        if os.path.exists(self.state_dir):
            try:
                shutil.rmtree(self.state_dir, ignore_errors=True)
            except Exception:
                pass
        if self.state_backup and os.path.exists(self.state_backup):
            try:
                shutil.copytree(self.state_backup, self.state_dir, dirs_exist_ok=True)
                shutil.rmtree(self.state_backup, ignore_errors=True)
            except Exception:
                pass

        # Restore backup files
        if self.session_backup and os.path.exists(self.session_backup):
            try:
                if os.path.exists(SESSION_FILE):
                    os.remove(SESSION_FILE)
                shutil.move(self.session_backup, SESSION_FILE)
            except Exception:
                pass
            
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
        project_sum = get_project_summary(proj_id)
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

    def test_accurate_token_estimation_and_database_normalization(self):
        import sqlite3
        import db
        # Create a mock transcript file representing multiple turns
        mock_log = "mock_transcript_accurate.jsonl"
        lines = [
            {"source": "USER_EXPLICIT", "content": "Start conversation", "type": "USER_INPUT"},
            # Model response (should trigger input and request_count increment)
            {"source": "MODEL", "content": "Response 1", "thinking": "Thinking 1", "type": "PLANNER_RESPONSE"},
            # Tool call / result (should NOT trigger request_count increment or prompt input accumulation)
            {"source": "SYSTEM", "content": "Tool output", "type": "TOOL_RESULT"},
            # Model response 2 (should trigger input and request_count increment)
            {"source": "MODEL", "content": "Response 2", "thinking": "Thinking 2", "type": "PLANNER_RESPONSE"},
        ]
        with open(mock_log, "w", encoding="utf-8") as f:
            for l in lines:
                f.write(json.dumps(l) + "\n")
                
        try:
            parsed = parse_transcript(mock_log)
            self.assertEqual(parsed["request_count"], 2)
            
            # Database normalization test
            # 1. Write an inflated legacy record
            db_path = "test_normalizer.db"
            if os.path.exists(db_path):
                os.remove(db_path)
            
            from db import save_usage_to_dbs, normalize_database_records
            # We save with simulated flat legacy payload representing massive values
            legacy_usage = {
                "input_tokens": 100000,
                "output_tokens": 50000,
                "cache_tokens": 10000,
                "thinking_tokens": 5000,
                "active_tokens": 20000,
                "total_tokens": 150000,
                "estimated_cost_usd": 1.5,
                "provider": "openai",
                "model": "gpt-4",
                "accuracy": "estimated"
            }
            
            # Mock configuration
            orig_project_db = db.PROJECT_DB
            db.PROJECT_DB = db_path
            try:
                save_usage_to_dbs("mock_conversation_123", "proj_123", "skill", "cmd", legacy_usage)
                
                # Check DB contents
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT total_tokens FROM usage_records WHERE conversation_id = 'mock_conversation_123'")
                total_tok = cursor.fetchone()[0]
                self.assertEqual(total_tok, 150000)
                conn.close()
                
                # Normalize database (since transcript doesn't exist for mock_conversation_123, it should scale down by 10)
                normalize_database_records(db_path)
                
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT total_tokens, input_tokens FROM usage_records WHERE conversation_id = 'mock_conversation_123'")
                row = cursor.fetchone()
                self.assertEqual(row[0], 15000)  # scaled down by 10
                self.assertEqual(row[1], 10000)  # scaled down by 10
                conn.close()
            finally:
                db.PROJECT_DB = orig_project_db
                if os.path.exists(db_path):
                    os.remove(db_path)
        finally:
            if os.path.exists(mock_log):
                os.remove(mock_log)

    def test_blueprint_registration_and_approval(self):
        # Initial empty session
        save_session_atomic({"checkpoint": 1})
        
        # Test registering blueprint via subprocess call to CLI
        import subprocess
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        
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
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        
        # Scenario 1: Raw bug request suggests quick-fix
        save_session_atomic({"checkpoint": 1})
        res = subprocess.run(
            [sys.executable, cli_path, "suggest", "--request", "Tôi bị crash ở hàm submit", "--recommend", "quick-fix"],
            capture_output=True, text=True
        )
        print("CLI STDOUT:", res.stdout)
        print("CLI STDERR:", res.stderr)
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
        print("S2 STDOUT:", res.stdout)
        print("S2 STDERR:", res.stderr)
        self.assertEqual(res.returncode, 0)
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
        save_session_atomic({"checkpoint": 8, "suggestion_gate": {}})
        session = load_session()
        self.assertNotEqual(session.get("suggestion_gate", {}).get("recommended_skill"), "implementation-to-release")
        
        # Scenario 10: Explicit /quick-fix bypasses suggestion gate and runs quick-fix normally
        save_session_atomic({"checkpoint": 1, "suggestion_gate": {}})
        # If running start for quick-fix directly
        res = subprocess.run(
            [sys.executable, cli_path, "start", "--skill", "quick-fix", "--command", "fix", "--checkpoint", "2", "--step", "Starting"],
            capture_output=True, text=True
        )
        for f in [self.lock_file, self.lease_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        self.assertEqual(res.returncode, 0)
        session = load_session()
        self.assertEqual(session["current_skill"], "quick-fix")
        self.assertEqual(session["suggestion_gate"]["active"], False)
        
        # Scenario 11: Explicit /brainstorm bypasses suggestion gate
        save_session_atomic({"checkpoint": 1})
        res = subprocess.run(
            [sys.executable, cli_path, "start", "--skill", "brainstorming", "--command", "brainstorm", "--checkpoint", "2", "--step", "Starting"],
            capture_output=True, text=True
        )
        for f in [self.lock_file, self.lease_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        session = load_session()
        self.assertEqual(session["current_skill"], "brainstorming")
        
        # Scenario 12: Explicit /release is allowed only as explicit release request
        save_session_atomic({"checkpoint": 9, "blueprint": {"approved": True}})
        res = subprocess.run(
            [sys.executable, cli_path, "start", "--skill", "implementation-to-release", "--command", "release", "--checkpoint", "10", "--step", "Releasing"],
            capture_output=True, text=True
        )
        for f in [self.lock_file, self.lease_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        session = load_session()
        self.assertEqual(session["current_skill"], "implementation-to-release")

    def test_permission_mode_scenarios(self):
        import subprocess
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        
        # S1: Default init sets sandbox
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        res = subprocess.run([sys.executable, cli_path, "init"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        session = load_session()
        self.assertEqual(session.get("permission_mode"), "sandbox")
        self.assertIn("permission_mode_selected_at", session)
        self.assertEqual(session.get("permission_mode_selected_by"), "user")
        
        # S2: Init --permission 1 sets sandbox
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        res = subprocess.run([sys.executable, cli_path, "init", "--permission", "1"], capture_output=True, text=True)
        session = load_session()
        self.assertEqual(session.get("permission_mode"), "sandbox")
        
        # S3: Init --permission 2 sets full_access
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        res = subprocess.run([sys.executable, cli_path, "init", "--permission", "2"], capture_output=True, text=True)
        session = load_session()
        self.assertEqual(session.get("permission_mode"), "full_access")

        # S3.1: Init --permission 3 with WRONG confirmation fallback to sandbox
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        res = subprocess.run(
            [sys.executable, cli_path, "init", "--permission", "3"],
            input="WRONG_CONFIRM\n", capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session.get("permission_mode"), "sandbox")

        # S3.2: Init --permission 3 with CORRECT confirmation sets unrestricted
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        res = subprocess.run(
            [sys.executable, cli_path, "init", "--permission", "3"],
            input="CONFIRM_UNRESTRICTED\n", capture_output=True, text=True
        )
        session = load_session()
        self.assertEqual(session.get("permission_mode"), "sandbox")
        
        # Import helpers inside test to test logic directly
        sys.path.append(os.path.dirname(cli_path))
        from workflow_runtime import requires_approval, get_permission_mode
        
        # S4: Sandbox mode requires approval for everything
        save_session_atomic({"permission_mode": "sandbox"})
        self.assertEqual(get_permission_mode(), "sandbox")
        self.assertEqual(requires_approval("normal_file_write"), True)
        self.assertEqual(requires_approval("source_code_change"), True)
        
        # S5: Full access mode bypasses normal file changes
        save_session_atomic({"permission_mode": "full_access"})
        self.assertEqual(get_permission_mode(), "full_access")
        self.assertEqual(requires_approval("normal_file_write"), False)
        self.assertEqual(requires_approval("source_code_change"), False)
        self.assertEqual(requires_approval("test_command"), False)
        
        # S6: Full access mode still locks release
        self.assertEqual(requires_approval("release"), True)
        
        # S7: Full access mode still locks git push/commit/tag
        self.assertEqual(requires_approval("git_push"), True)
        self.assertEqual(requires_approval("git_commit"), True)
        self.assertEqual(requires_approval("git_tag"), True)
        
        # S8: Fallback on corrupted value
        save_session_atomic({"permission_mode": "corrupted_mode"})
        self.assertEqual(get_permission_mode(), "sandbox")
        self.assertEqual(requires_approval("normal_file_write"), True)
        
        # S9: Changing permission mode is hard-gated
        self.assertEqual(requires_approval("permission_mode_change"), True)

        # S9.1: Unrestricted mode bypasses absolutely everything
        save_session_atomic({"permission_mode": "unrestricted"})
        self.assertEqual(get_permission_mode(), "unrestricted")
        self.assertEqual(requires_approval("normal_file_write"), False)
        self.assertEqual(requires_approval("source_code_change"), False)
        self.assertEqual(requires_approval("git_push"), False)
        self.assertEqual(requires_approval("release"), False)
        self.assertEqual(requires_approval("permission_mode_change"), False)

    def test_cli_compact_creates_snapshot(self):
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        snapshot_file = os.path.join(".agents", "runtime", "context_snapshot.json")
        
        # Ensure clean state
        if os.path.exists(snapshot_file):
            os.remove(snapshot_file)
            
        try:
            # Create a mock session
            mock_session = {
                "checkpoint": 3,
                "status": "in_progress",
                "current_skill": "initialize-workflow",
                "current_command": "init",
                "current_step": "Running initialization test"
            }
            save_session_atomic(mock_session)
            
            # Execute compact subcommand
            import subprocess
            res = subprocess.run(
                [sys.executable, cli_path, "compact"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(snapshot_file))
            
            # Load and verify snapshot
            with open(snapshot_file, "r", encoding="utf-8") as f:
                snapshot = json.load(f)
                
            self.assertEqual(snapshot.get("checkpoint"), 3)
            self.assertEqual(snapshot.get("current_skill"), "initialize-workflow")
            self.assertEqual(snapshot.get("active_feature_id"), "FIX-014")
            self.assertIn("rollover_requested_at", snapshot)
        finally:
            if os.path.exists(snapshot_file):
                os.remove(snapshot_file)

    def test_execution_modes_and_persistence(self):
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
        tasks_file = os.path.join(".agents", "runtime", "parallel-tasks.json")
        locks_file = os.path.join(".agents", "runtime", "file-locks.json")
        conflicts_file = os.path.join(".agents", "runtime", "conflicts.json")
        
        try:
            # Create a mock session with checkpoint 5 to allow parallel mode during implementation
            mock_session = {
                "checkpoint": 5,
                "status": "in_progress",
                "current_skill": "orchestrator",
                "current_command": "orchestrate",
                "current_step": "Testing implementation execution modes"
            }
            save_session_atomic(mock_session)

            # 1. Test execution recommend command
            import subprocess
            res = subprocess.run(
                [sys.executable, cli_path, "execution", "recommend", "--mode", "parallel", "--reason", "Independent files"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(plan_file))
            
            with open(plan_file, "r", encoding="utf-8") as f:
                plan = json.load(f)
            self.assertEqual(plan.get("execution_mode"), "pending")
            self.assertEqual(plan.get("recommended_mode"), "sequential")
            self.assertEqual(plan.get("recommended_reason"), "Parallel execution is completely disabled in this framework. Sequential execution only.")
            self.assertFalse(plan.get("approved"))
            
            # 2. Test execution mode command
            res = subprocess.run(
                [sys.executable, cli_path, "execution", "mode", "--mode", "parallel", "--approve"],
                capture_output=True, text=True
            )
            # Parallel mode should FAIL now
            self.assertEqual(res.returncode, 1)
            self.assertIn("Parallel execution mode is disabled. Only sequential execution is supported.", res.stderr)
            
            # 3. Test execution summary command
            res = subprocess.run(
                [sys.executable, cli_path, "execution", "summary"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("Sequential Workflow Engine mode", res.stdout)
            
            # 4. Test file lock acquire & release
            res = subprocess.run(
                [sys.executable, cli_path, "lock", "acquire", "--task-id", "task-1", "--files", "file1.txt,file2.txt"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(locks_file))
            
            with open(locks_file, "r", encoding="utf-8") as f:
                locks = json.load(f).get("locks", {})
            self.assertIn("file1.txt", locks)
            self.assertEqual(locks["file1.txt"].get("task_id"), "task-1")
            
            # Conflict lock acquisition should fail
            res = subprocess.run(
                [sys.executable, cli_path, "lock", "acquire", "--task-id", "task-2", "--files", "file1.txt"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 1)
            
            # Release lock
            res = subprocess.run(
                [sys.executable, cli_path, "lock", "release", "--task-id", "task-1"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            with open(locks_file, "r", encoding="utf-8") as f:
                locks = json.load(f).get("locks", {})
            self.assertNotIn("file1.txt", locks)
            
            # 5. Test task plan, start, complete, fail
            with open(plan_file, "w", encoding="utf-8") as f:
                json.dump({"tasks": [{"task_id": "t-1"}, {"task_id": "t-2"}]}, f, indent=2)
                
            res = subprocess.run(
                [sys.executable, cli_path, "task", "plan"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            self.assertTrue(os.path.exists(tasks_file))
            
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f).get("tasks", {})
            self.assertEqual(tasks.get("t-1", {}).get("status"), "pending")
            
            res = subprocess.run(
                [sys.executable, cli_path, "task", "start", "--task-id", "t-1"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks = json.load(f).get("tasks", {})
            self.assertEqual(tasks.get("t-1", {}).get("status"), "running")
            
        finally:
            for fpath in [plan_file, tasks_file, locks_file, conflicts_file]:
                if os.path.exists(fpath):
                    os.remove(fpath)

    def test_parallel_scope_constraints(self):
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
        session_file = os.path.join(".agents", ".session.json")
        
        # Clean state
        if os.path.exists(plan_file):
            os.remove(plan_file)
            
        # Back up existing session
        session_backup = None
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_backup = json.load(f)
            except Exception:
                pass
                
        try:
            # Case 1: Checkpoint < 5 (e.g. Checkpoint 3 - Brainstorming)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump({"checkpoint": 3, "current_skill": "brainstorming"}, f, indent=2)
                
            # 1. Recommend parallel mode - should force to sequential
            import subprocess
            res = subprocess.run(
                [sys.executable, cli_path, "execution", "recommend", "--mode", "parallel", "--reason", "Independent"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            
            with open(plan_file, "r", encoding="utf-8") as f:
                plan = json.load(f)
            self.assertFalse(plan.get("parallel_allowed"))
            self.assertEqual(plan.get("recommended_mode"), "sequential")
            
            # 2. Mode parallel approval should FAIL (returncode = 1) because parallel is disabled
            res = subprocess.run(
                [sys.executable, cli_path, "execution", "mode", "--mode", "parallel", "--approve"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 1)
            self.assertIn("Parallel execution mode is disabled. Only sequential execution is supported.", res.stderr)
            
            # Case 2: Checkpoint >= 5 (e.g. Checkpoint 5 - Blueprint approved / Implementation)
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump({"checkpoint": 5, "current_skill": "orchestrator"}, f, indent=2)
                
            res = subprocess.run(
                [sys.executable, cli_path, "execution", "recommend", "--mode", "parallel", "--reason", "Independent"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 0)
            with open(plan_file, "r", encoding="utf-8") as f:
                plan = json.load(f)
            self.assertFalse(plan.get("parallel_allowed"))
            self.assertEqual(plan.get("recommended_mode"), "sequential")
            
            # Mode parallel approval should still FAIL
            res = subprocess.run(
                [sys.executable, cli_path, "execution", "mode", "--mode", "parallel", "--approve"],
                capture_output=True, text=True
            )
            self.assertEqual(res.returncode, 1)
            self.assertIn("Parallel execution mode is disabled. Only sequential execution is supported.", res.stderr)
            
        finally:
            if os.path.exists(plan_file):
                os.remove(plan_file)
            if session_backup:
                try:
                    with open(session_file, "w", encoding="utf-8") as f:
                        json.dump(session_backup, f, indent=2)
                except Exception:
                    pass
            elif os.path.exists(session_file):
                os.remove(session_file)

    def test_analysis_agent_lifecycle(self):
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        session_file = SESSION_FILE
        analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
        
        # Ensure clean state
        if os.path.exists(analysis_file):
            try:
                os.remove(analysis_file)
            except Exception:
                pass
            
        try:
            # Initialize a session for testing
            save_session_atomic({"checkpoint": 3, "active_skill": "brainstorming"})
            
            # 1. Add analysis agent
            res = subprocess.run([
                sys.executable, cli_path, "analysis-agent", "add",
                "--agent-id", "test_ux_1",
                "--role", "UX Specialist",
                "--status", "running",
                "--summary", "Checking UI layout design",
                "--recommendations", '["Fix contrast", "Add spacing"]'
            ], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            
            # Verify file created
            self.assertTrue(os.path.exists(analysis_file))
            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data["agents"]), 1)
            self.assertEqual(data["agents"][0]["agent_id"], "test_ux_1")
            self.assertEqual(data["agents"][0]["role"], "UX Specialist")
            self.assertEqual(data["agents"][0]["recommendations"], ["Fix contrast", "Add spacing"])
            
            # Verify sync to session
            session = load_session()
            self.assertEqual(len(session.get("analysis_agents", [])), 1)
            self.assertEqual(session["analysis_agents"][0]["agent_id"], "test_ux_1")
            
            # 2. Add another agent
            res = subprocess.run([
                sys.executable, cli_path, "analysis-agent", "add",
                "--agent-id", "test_sec_2",
                "--role", "Security Specialist",
                "--status", "completed",
                "--summary", "Verifying token leakage",
                "--recommendations", '["Secure localStorage"]'
            ], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            
            # 3. Merge agents
            res = subprocess.run([
                sys.executable, cli_path, "analysis-agent", "merge"
            ], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertIn("UX Specialist", res.stdout)
            self.assertIn("Security Specialist", res.stdout)
            self.assertIn("[UX Specialist] Fix contrast", res.stdout)
            
            # 4. Clear agents
            res = subprocess.run([
                sys.executable, cli_path, "analysis-agent", "clear"
            ], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(len(data["agents"]), 0)
            
            # Verify session also cleared
            session = load_session()
            self.assertEqual(len(session.get("analysis_agents", [])), 0)
            
        finally:
            if os.path.exists(analysis_file):
                try:
                    os.remove(analysis_file)
                except Exception:
                    pass


    def test_start_implementation_without_approved_blueprint(self):
        cli_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "workflow_runtime.py")
        
        # 1. Setup session with unapproved blueprint
        session = {
            "workspace": {"path": ".", "valid": True},
            "git": {"is_git_repository": True, "branch": "main", "working_tree": "clean"},
            "work_item": {"type": "FEAT", "id": "FEAT-001", "title": "Initial Scaffolding"},
            "version": {"version": "1.0.0", "source": "MANIFEST.json"},
            "checkpoint": 1,
            "blueprint": {
                "path": "docs/designs/test_blueprint.md",
                "exists": True,
                "approved": False
            }
        }
        save_session_atomic(session)
        
        # 2. Try starting implementation - should fail
        res = subprocess.run([
            sys.executable, cli_path, "start",
            "--skill", "blueprint-to-implementation",
            "--command", "implement",
            "--checkpoint", "6",
            "--step", "Testing implementation start"
        ], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Blueprint is not approved", res.stderr)
        
        # 3. Approve the blueprint and try again - should pass
        session["blueprint"]["approved"] = True
        save_session_atomic(session)
        
        res = subprocess.run([
            sys.executable, cli_path, "start",
            "--skill", "blueprint-to-implementation",
            "--command", "implement",
            "--checkpoint", "6",
            "--step", "Testing implementation start"
        ], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        
        updated_session = load_session()
        self.assertEqual(updated_session["current_skill"], "blueprint-to-implementation")
        self.assertEqual(updated_session["checkpoint"], 6)

    def test_load_workflow_config_defaults(self):
        # Temp path setup to make sure we don't read actual config if it exists
        config_path = os.path.join(".agents", "workflow.config.json")
        backup_path = config_path + ".unittest_bak"
        if os.path.exists(config_path):
            os.rename(config_path, backup_path)
            
        try:
            from session import load_workflow_config
            cfg = load_workflow_config()
            self.assertEqual(cfg["git_flow"]["development_branch"], "main")
            self.assertEqual(cfg["git_flow"]["sync_method"], "merge")
        finally:
            if os.path.exists(backup_path):
                os.rename(backup_path, config_path)

    def test_load_workflow_config_custom(self):
        config_path = os.path.join(".agents", "workflow.config.json")
        backup_path = config_path + ".unittest_bak"
        if os.path.exists(config_path):
            os.rename(config_path, backup_path)
            
        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            custom_data = {
                "project_name": "test-project",
                "git_flow": {
                    "development_branch": "dev",
                    "sync_method": "rebase"
                }
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(custom_data, f)
                
            from session import load_workflow_config
            cfg = load_workflow_config()
            self.assertEqual(cfg["project_name"], "test-project")
            self.assertEqual(cfg["git_flow"]["development_branch"], "dev")
            self.assertEqual(cfg["git_flow"]["sync_method"], "rebase")
            # Should inherit other default fields
            self.assertEqual(cfg["git_flow"]["release_branch"], "main")
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)
            if os.path.exists(backup_path):
                os.rename(backup_path, config_path)

    def test_telemetry_config_loading_and_fallback(self):
        # 1. Setup session with mock data
        session = {
            "workspace": {"path": ".", "valid": True},
            "git": {"is_git_repository": True, "branch": "main", "working_tree": "clean"},
            "work_item": {"type": "FEAT", "id": "FEAT-001", "title": "Initial Scaffolding"},
            "version": {"version": "1.0.0", "source": "MANIFEST.json"},
            "checkpoint": 1
        }
        
        # Backup config
        config_path = os.path.join(".agents", "workflow.config.json")
        backup_path = config_path + ".unittest_bak"
        if os.path.exists(config_path):
            os.rename(config_path, backup_path)
            
        try:
            # Test 1: No config file -> should load defaults
            from unittest.mock import patch
            from workflow_runtime import update_context_health
            
            with patch('analytics_engine.update_analytics') as mock_analytics, \
                 patch('workflow_runtime.get_project_summary') as mock_project_summary, \
                 patch('workflow_runtime.get_global_summary') as mock_global_summary, \
                 patch('workflow_runtime.save_usage_to_dbs'):
                 
                 mock_analytics.return_value = {
                     "active_context": {"total_tokens": 120000, "limit_tokens": 1000000, "percentage": 12.0},
                     "accumulated_usage": {"total_tokens": 120000}
                 }
                 mock_project_summary.return_value = {"total_tokens": 120000}
                 mock_global_summary.return_value = {"total_tokens": 120000}
                 
                 update_context_health(session)
                 
            self.assertIn("telemetry_config", session)
            self.assertEqual(session["telemetry_config"]["context_thresholds"]["warning"], 60)
            self.assertEqual(session["telemetry_config"]["cost_thresholds"]["warning_usd"], 50.0)
            self.assertIn("context_styles", session["telemetry_config"])
            self.assertEqual(session["telemetry_config"]["context_styles"]["healthy"]["color"], "#10b981")
            
            # Test 2: Custom config file with custom telemetry
            custom_data = {
                "project_name": "test-project",
                "telemetry": {
                    "context_thresholds": {
                        "warning": 50,
                        "high": 75,
                        "critical": 90
                    },
                    "context_styles": {
                        "healthy": {
                            "color": "#00ff00",
                            "bg": "rgba(0, 255, 0, 0.1)",
                            "border": "rgba(0, 255, 0, 0.3)",
                            "icon": "🟢",
                            "label": "All Good"
                        }
                    },
                    "cost_thresholds": {
                        "warning_usd": 5.0,
                        "critical_usd": 25.0
                    }
                }
            }
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(custom_data, f)
                
            session_custom = {
                "workspace": {"path": ".", "valid": True},
                "git": {"is_git_repository": True, "branch": "main", "working_tree": "clean"},
                "work_item": {"type": "FEAT", "id": "FEAT-001", "title": "Initial Scaffolding"},
                "version": {"version": "1.0.0", "source": "MANIFEST.json"},
                "checkpoint": 1
            }
            
            with patch('analytics_engine.update_analytics') as mock_analytics, \
                 patch('workflow_runtime.get_project_summary') as mock_project_summary, \
                 patch('workflow_runtime.get_global_summary') as mock_global_summary, \
                 patch('workflow_runtime.save_usage_to_dbs'):
                 
                 mock_analytics.return_value = {
                     "active_context": {"total_tokens": 120000, "limit_tokens": 1000000, "percentage": 12.0},
                     "accumulated_usage": {"total_tokens": 120000}
                 }
                 mock_project_summary.return_value = {"total_tokens": 120000}
                 mock_global_summary.return_value = {"total_tokens": 120000}
                 
                 update_context_health(session_custom)
                 
            self.assertEqual(session_custom["telemetry_config"]["context_thresholds"]["warning"], 50)
            self.assertEqual(session_custom["telemetry_config"]["context_thresholds"]["high"], 75)
            self.assertEqual(session_custom["telemetry_config"]["cost_thresholds"]["warning_usd"], 5.0)
            self.assertEqual(session_custom["telemetry_config"]["context_styles"]["healthy"]["color"], "#00ff00")
            self.assertEqual(session_custom["telemetry_config"]["context_styles"]["healthy"]["label"], "All Good")
            
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)
            if os.path.exists(backup_path):
                os.rename(backup_path, config_path)


if __name__ == "__main__":
    unittest.main()
