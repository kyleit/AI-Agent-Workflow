# test_suggested_next_skill_output.py
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agents", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator

class TestSuggestedNextSkillOutput(unittest.TestCase):
    @patch("coordinator.get_state_store")
    def test_suggested_keys_present(self, mock_get_store):
        mock_store = MagicMock()
        mock_store.get.return_value = {}
        mock_get_store.return_value = mock_store
        
        coord = WorkflowCoordinator()
        res = coord.run_tick("fix ticket 12")
        self.assertIn("suggested_next_skill", res)
        self.assertIn("suggested_next_command", res)
        self.assertTrue(res["suggested_next_skill"])
        self.assertTrue(res["suggested_next_command"])

if __name__ == "__main__":
    unittest.main()
