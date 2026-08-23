# test_no_auto_parallel_selection.py
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agents", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator, ParallelGateViolationError

class TestNoAutoParallelSelection(unittest.TestCase):
    @patch("coordinator.get_state_store")
    def test_parallel_triggers_halt(self, mock_get_store):
        mock_store = MagicMock()
        mock_store.get.return_value = {}
        mock_get_store.return_value = mock_store
        
        coord = WorkflowCoordinator()
        with self.assertRaises(ParallelGateViolationError):
            coord.run_tick("run implementation in parallel mode")

if __name__ == "__main__":
    unittest.main()
