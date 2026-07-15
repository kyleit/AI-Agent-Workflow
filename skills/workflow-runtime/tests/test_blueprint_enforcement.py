# test_blueprint_enforcement.py
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agents", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator

class TestBlueprintEnforcement(unittest.TestCase):
    @patch("coordinator.get_state_store")
    def test_verify_blueprint_gate(self, mock_get_store):
        mock_store = MagicMock()
        mock_store.get.return_value = {
            "blueprint": {
                "approved": True
            }
        }
        mock_get_store.return_value = mock_store
        
        coord = WorkflowCoordinator()
        self.assertTrue(coord._verify_blueprint_gate("FEAT-404"))
        
    @patch("coordinator.get_state_store")
    def test_verify_blueprint_gate_false(self, mock_get_store):
        mock_store = MagicMock()
        mock_store.get.return_value = {
            "blueprint": {
                "approved": False
            }
        }
        mock_get_store.return_value = mock_store
        
        coord = WorkflowCoordinator()
        self.assertFalse(coord._verify_blueprint_gate("FEAT-404"))

if __name__ == "__main__":
    unittest.main()
