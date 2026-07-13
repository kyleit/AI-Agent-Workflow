# test_autonomous_approval_bypass.py
import unittest
import os
import sys
import json
import shutil
import tempfile
from unittest.mock import patch, MagicMock

# Add scripts path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

import workflow_runtime as wr

class TestAutonomousApprovalBypass(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.session_path = os.path.join(self.temp_dir, "session.json")
        self.pending_path = os.path.join(self.temp_dir, "pending-choice.json")
        self.response_path = os.path.join(self.temp_dir, "choice-response.json")
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @patch("workflow_runtime.load_session")
    def test_bypass_intermediate_gate_in_autonomous_mode(self, mock_load):
        # Setup session with autonomous_delivery = True
        mock_load.return_value = {
            "autonomous_delivery": True,
            "work_item": {"id": "FEAT-117"}
        }
        
        # Mock args
        args = MagicMock()
        args.subaction = "wait"
        args.id = "blueprint_approval"
        args.timeout = 5
        args.type = "approval"
        
        # Execute wait subaction with patch on os.path structures
        original_join = os.path.join
        with patch("os.path.join") as mock_join:
            # Route paths to temp folder
            mock_join.side_effect = lambda *parts: original_join(self.temp_dir, parts[-1])
            
            # Create a pending choice
            with open(self.pending_path, "w", encoding="utf-8") as f:
                json.dump({"type": "approval", "id": "blueprint_approval"}, f)
                
            wr.do_choice(args)
            
            # Verification: should create response with 'approve' and resolve instantly
            self.assertTrue(os.path.exists(self.response_path))
            with open(self.response_path, "r", encoding="utf-8") as f:
                res = json.load(f)
            self.assertEqual(res["selected"], "approve")
            self.assertFalse(res["cancelled"])

    @patch("workflow_runtime.load_session")
    def test_protected_gate_not_bypassed(self, mock_load):
        # Setup session with autonomous_delivery = True
        mock_load.return_value = {
            "autonomous_delivery": True,
            "work_item": {"id": "FEAT-117"}
        }
        
        args = MagicMock()
        args.subaction = "wait"
        args.id = "release_approval" # Protected gate
        args.timeout = 1
        args.type = "approval"
        
        original_join = os.path.join
        with patch("os.path.join") as mock_join:
            mock_join.side_effect = lambda *parts: original_join(self.temp_dir, parts[-1])
            
            with open(self.pending_path, "w", encoding="utf-8") as f:
                json.dump({"type": "approval", "id": "release_approval"}, f)
                
            # It should not bypass, and since stdin is not interactive, it will fallback to auto-select 'cancel'
            wr.do_choice(args)
            
            self.assertTrue(os.path.exists(self.response_path))
            with open(self.response_path, "r", encoding="utf-8") as f:
                res = json.load(f)
            # Protected gate does NOT auto-approve, so fallback sets to 'cancel'
            self.assertEqual(res["selected"], "cancel")

if __name__ == "__main__":
    unittest.main()
