# test_runtime.py
import unittest
import os
import sys
import shutil
import json
import uuid

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from session import load_session, save_session_atomic, SESSION_FILE
from checkpoint import validate_checkpoint_level, get_checkpoint_name
from validator import get_git_info, get_version_info
from drift import check_context_drift
from heartbeat import generate_heartbeat_string
from context import estimate_context_usage

class TestRuntimeEngine(unittest.TestCase):
    def setUp(self):
        # Back up existing session file if it exists
        self.session_backup = None
        if os.path.exists(SESSION_FILE):
            self.session_backup = SESSION_FILE + ".bak"
            shutil.copy2(SESSION_FILE, self.session_backup)
            os.remove(SESSION_FILE)
            
    def tearDown(self):
        # Restore backup session file
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        if self.session_backup and os.path.exists(self.session_backup):
            shutil.move(self.session_backup, SESSION_FILE)
            
    def test_atomic_write_and_missing_session(self):
        # Test loading missing session
        session = load_session()
        self.assertEqual(session, {})
        
        # Test atomic write
        test_data = {"checkpoint": 2, "status": "completed"}
        save_session_atomic(test_data)
        
        loaded = load_session()
        self.assertEqual(loaded["checkpoint"], 2)
        self.assertEqual(loaded["status"], "completed")
        self.assertIn("conversation_id", loaded)
        
    def test_conversation_preservation(self):
        conv_id = str(uuid.uuid4())
        save_session_atomic({"conversation_id": conv_id})
        
        # Write again, confirm preservation
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
        # Corrupt the session file
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            f.write("{invalid json")
            
        # Verify it loads as empty dict rather than crashing
        session = load_session()
        self.assertEqual(session, {})

if __name__ == "__main__":
    unittest.main()
