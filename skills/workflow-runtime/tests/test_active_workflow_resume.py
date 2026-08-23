# test_active_workflow_resume.py
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agents", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator

class TestActiveWorkflowResume(unittest.TestCase):
    @patch("coordinator.get_state_store")
    def test_resume_priority(self, mock_get_store):
        mock_store = MagicMock()
        mock_store.get.return_value = {
            "active_workflow": "standard-development",
            "suggested_next_skill": "quick-fix",
            "suggested_next_command": "fix"
        }
        mock_get_store.return_value = mock_store
        
        coord = WorkflowCoordinator()
        should_resume, skill, cmd = coord._check_resume_priority()
        self.assertTrue(should_resume)
        self.assertEqual(skill, "quick-fix")
        self.assertEqual(cmd, "fix")

if __name__ == "__main__":
    unittest.main()
