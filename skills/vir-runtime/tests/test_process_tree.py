# File path: tests/unit/test_process_tree.py
import unittest
import subprocess
import time
import os
from vir_runtime.sandbox.process import WindowsProcessManager

class TestProcessTree(unittest.TestCase):
    def test_terminate_process_tree(self):
        # Spawn a dummy process that runs a sleep command
        # Using python to run a sleep loop so it works on both Windows and Unix
        proc = subprocess.Popen(
            ["python", "-c", "import time; [time.sleep(1) for _ in range(30)]"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        pid = proc.pid

        # Verify the process is running
        self.assertIsNone(proc.poll())

        # Terminate process tree
        WindowsProcessManager.terminate_process_tree(pid)
        time.sleep(0.5)

        # Verify the process has terminated
        self.assertIsNotNone(proc.poll())

if __name__ == "__main__":
    unittest.main()
