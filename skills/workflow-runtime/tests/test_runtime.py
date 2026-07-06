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

if __name__ == "__main__":
    unittest.main()
