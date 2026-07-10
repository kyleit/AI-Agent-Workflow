# test_choice.py
import unittest
import os
import sys
import shutil
import json
from unittest.mock import patch
import io

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from session import load_session, save_session_atomic, SESSION_FILE
from workflow_runtime import do_choice

class DummyArgs:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class TestChoiceProtocol(unittest.TestCase):
    def setUp(self):
        self.runtime_dir = os.path.join(".agents", "runtime")
        os.makedirs(self.runtime_dir, exist_ok=True)
        self.pending_path = os.path.join(self.runtime_dir, "pending-choice.json")
        self.response_path = os.path.join(self.runtime_dir, "choice-response.json")
        self.ui_capabilities_path = os.path.join(self.runtime_dir, "ui-capabilities.json")
        
        # Back up existing session file
        self.session_backup = None
        if os.path.exists(SESSION_FILE):
            self.session_backup = SESSION_FILE + ".bak"
            shutil.copy2(SESSION_FILE, self.session_backup)
            os.remove(SESSION_FILE)

        # Ensure clean state
        for p in [self.pending_path, self.response_path, self.ui_capabilities_path]:
            if os.path.exists(p):
                os.remove(p)
                
        # Initialize default session for commands
        save_session_atomic({"checkpoint": 4, "status": "in_progress"})
        
    def tearDown(self):
        for p in [self.pending_path, self.response_path, self.ui_capabilities_path, SESSION_FILE]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        if self.session_backup and os.path.exists(self.session_backup):
            shutil.move(self.session_backup, SESSION_FILE)

    def test_create_choice_list(self):
        args = DummyArgs(
            subaction="create",
            id="test_choice_1",
            title="Test Title",
            desc="Test Description",
            options="opt1,opt2,opt3",
            type="choice",
            allow_cancel=True,
            required=True
        )
        do_choice(args)
        
        self.assertTrue(os.path.exists(self.pending_path))
        with open(self.pending_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["id"], "test_choice_1")
        self.assertEqual(data["title"], "Test Title")
        self.assertEqual(len(data["options"]), 3)
        self.assertEqual(data["options"][0]["id"], "opt1")

    def test_create_choice_json(self):
        opts_json = '[{"id":"a","label":"Option A"},{"id":"b","label":"Option B"}]'
        args = DummyArgs(
            subaction="create",
            id="test_choice_json",
            title="Test JSON",
            desc="",
            options=opts_json,
            type="choice",
            allow_cancel=False,
            required=False
        )
        do_choice(args)
        
        self.assertTrue(os.path.exists(self.pending_path))
        with open(self.pending_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["id"], "test_choice_json")
        self.assertEqual(len(data["options"]), 2)
        self.assertEqual(data["options"][0]["id"], "a")

    def test_read_and_clear_choice(self):
        resp_payload = {
            "id": "my_choice",
            "selected": "opt2",
            "cancelled": False
        }
        with open(self.response_path, "w", encoding="utf-8") as f:
            json.dump(resp_payload, f)
            
        args_read = DummyArgs(subaction="read", id="my_choice")
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            do_choice(args_read)
            self.assertEqual(fake_out.getvalue().strip(), "opt2")
            
        args_clear = DummyArgs(subaction="clear")
        do_choice(args_clear)
        self.assertFalse(os.path.exists(self.response_path))

    def test_fallback_mode_stdin(self):
        # Setup pending choice
        opts_json = '[{"id":"opt_y","label":"Yes"},{"id":"opt_n","label":"No"}]'
        args_create = DummyArgs(
            subaction="create",
            id="stdin_choice",
            title="Stdin Test",
            desc="Enter 1 or 2",
            options=opts_json,
            type="choice",
            allow_cancel=False,
            required=True
        )
        do_choice(args_create)
        
        # Check stdin selection 1 -> opt_y
        args_wait = DummyArgs(subaction="wait", id="stdin_choice", timeout=5)
        
        with patch('builtins.input', return_value="1"), patch('sys.stdout', new=io.StringIO()):
            do_choice(args_wait)
            
        self.assertTrue(os.path.exists(self.response_path))
        with open(self.response_path, "r", encoding="utf-8") as f:
            resp = json.load(f)
        self.assertEqual(resp["id"], "stdin_choice")
        self.assertEqual(resp["selected"], "opt_y")

    def test_ui_capability_interactive_resolution(self):
        # Enable UI
        with open(self.ui_capabilities_path, "w", encoding="utf-8") as f:
            json.dump({"interactive_choice": True}, f)
            
        # Create choice
        args_create = DummyArgs(
            subaction="create",
            id="ui_choice",
            title="UI Test",
            desc="",
            options="opt1,opt2",
            type="choice",
            allow_cancel=True,
            required=True
        )
        do_choice(args_create)
        
        # Write response concurrently using mock/timeout
        resp_payload = {
            "id": "ui_choice",
            "selected": "opt2",
            "cancelled": False
        }
        with open(self.response_path, "w", encoding="utf-8") as f:
            json.dump(resp_payload, f)
            
        args_wait = DummyArgs(subaction="wait", id="ui_choice", timeout=2)
        with patch('sys.stdout', new=io.StringIO()) as fake_out:
            do_choice(args_wait)
            self.assertIn("Choice resolved: opt2", fake_out.getvalue())

if __name__ == "__main__":
    unittest.main()
