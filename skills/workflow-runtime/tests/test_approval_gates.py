# test_approval_gates.py
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agents", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator, GateViolationError

class TestApprovalGates(unittest.TestCase):
    @patch("coordinator.get_state_store")
    def test_verify_safety_gates_raise(self, mock_get_store):
        mock_store = MagicMock()
        mock_store.get.return_value = {
            "blueprint": {
                "approved": False
            }
        }
        mock_get_store.return_value = mock_store
        
        coord = WorkflowCoordinator()
        with self.assertRaises(GateViolationError):
            coord._verify_safety_gates("blueprint-to-implementation", "implementation")

if __name__ == "__main__":
    unittest.main()
