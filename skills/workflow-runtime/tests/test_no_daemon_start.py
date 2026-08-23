# test_no_daemon_start.py
import os
import sys
import unittest
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agents", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator

class TestNoDaemonStart(unittest.TestCase):
    def test_no_daemon_threads(self):
        pre_threads = [t for t in threading.enumerate() if t.daemon]
        # Coordinator should not start any daemon thread during initialization or operation
        coord = WorkflowCoordinator()
        self.assertEqual(len([t for t in threading.enumerate() if t.daemon]), len(pre_threads))

if __name__ == "__main__":
    unittest.main()
