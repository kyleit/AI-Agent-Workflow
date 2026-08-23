# test_runtime_gate.py
import unittest
import os
import sys
import shutil
import json

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from session import load_session, save_session_atomic, SESSION_FILE
from workflow_runtime import (
    RuntimeInputGate, 
    ForbiddenAISourceError, 
    InvalidResumeTokenError
)

class TestRuntimeInputGate(unittest.TestCase):
    def setUp(self):
        os.environ["TESTING"] = "1"
        
        # Back up existing session file if any
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

        # Create a fresh clean session
        save_session_atomic({
            "workspace": {"path": ".", "valid": True},
            "checkpoint": 1,
            "status": "in_progress",
            "current_logs": []
        })

    def tearDown(self):
        # Clean up session files and restore backups
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except Exception:
                pass
        if self.session_backup and os.path.exists(self.session_backup):
            try:
                shutil.copy2(self.session_backup, SESSION_FILE)
                os.remove(self.session_backup)
            except Exception:
                pass
                
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

    def test_enter_waiting_state(self):
        pending = RuntimeInputGate.enter_waiting_state(
            prompt_id="test_prompt",
            question="Choose mode?",
            options=["A", "B"]
        )
        
        self.assertEqual(pending["input_id"], "test_prompt")
        self.assertEqual(pending["question"], "Choose mode?")
        self.assertEqual(pending["options"], ["A", "B"])
        self.assertIsNotNone(pending["resume_token"])
        
        session = load_session()
        self.assertEqual(session["status"], "waiting_input")
        self.assertEqual(session["pending_input"]["input_id"], "test_prompt")

    def test_submit_input_success(self):
        pending = RuntimeInputGate.enter_waiting_state(
            prompt_id="test_prompt",
            question="Choose mode?",
            options=["A", "B"]
        )
        
        token = pending["resume_token"]
        success = RuntimeInputGate.submit_input(
            prompt_id="test_prompt",
            value="A",
            source="cli_user",
            token=token
        )
        
        self.assertTrue(success)
        session = load_session()
        self.assertEqual(session["status"], "completed")
        self.assertIsNone(session.get("pending_input"))

    def test_submit_input_forbidden_ai_source(self):
        pending = RuntimeInputGate.enter_waiting_state(
            prompt_id="test_prompt",
            question="Choose mode?",
            options=["A", "B"]
        )
        
        token = pending["resume_token"]
        with self.assertRaises(ForbiddenAISourceError):
            RuntimeInputGate.submit_input(
                prompt_id="test_prompt",
                value="A",
                source="ai",
                token=token
            )
            
        session = load_session()
        self.assertEqual(session["status"], "waiting_input")
        self.assertIsNotNone(session.get("pending_input"))

    def test_submit_input_invalid_token(self):
        pending = RuntimeInputGate.enter_waiting_state(
            prompt_id="test_prompt",
            question="Choose mode?",
            options=["A", "B"]
        )
        
        with self.assertRaises(InvalidResumeTokenError):
            RuntimeInputGate.submit_input(
                prompt_id="test_prompt",
                value="A",
                source="cli_user",
                token="wrong_token"
            )
            
        session = load_session()
        self.assertEqual(session["status"], "waiting_input")
        self.assertIsNotNone(session.get("pending_input"))

if __name__ == "__main__":
    unittest.main()
