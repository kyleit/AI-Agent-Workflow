"""
test_hardening_regression.py — Regression tests for FEAT-050-053 hardening campaign.
Checks file lock ownership safeguards, concurrency self-blocking fixes, and robust process tree cleanup.
"""
import os
import sys
import time
import subprocess
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
import importlib.util

# Load RuntimeTestBase dynamically from fixtures/conftest.py
fixtures_conftest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures", "conftest.py"))
spec = importlib.util.spec_from_file_location("fixtures_conftest", fixtures_conftest_path)
if spec and spec.loader:
    fixtures_conftest = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures_conftest)
    RuntimeTestBase = fixtures_conftest.RuntimeTestBase
else:
    raise ImportError("Could not load RuntimeTestBase from fixtures/conftest.py")

from session import OSFileLock
from hierarchical_runtime import HierarchicalRuntime
from test_coordinator import kill_process_tree

class HardeningRegressionTests(RuntimeTestBase):

    # Regression 1: CLI status/init must not delete lock of running daemon
    def test_cli_status_does_not_clear_running_daemon_lock(self):
        lock_path = os.path.join(self.workspace, "orchestrator.lock")
        
        # 1. Daemon acquires the lock
        daemon_lock = OSFileLock(lock_path)
        acquired = daemon_lock.acquire()
        self.assertTrue(acquired)
        self.assertTrue(os.path.exists(lock_path))

        # 2. CLI attempts to acquire the lock (should fail)
        cli_lock = OSFileLock(lock_path)
        cli_acquired = cli_lock.acquire()
        self.assertFalse(cli_acquired)
        
        # 3. Verify lock file STILL exists on disk (the critical bug fix check)
        self.assertTrue(os.path.exists(lock_path), "CLI must not release/delete daemon's lock file on failed acquire.")

        # 4. Cleanup
        daemon_lock.release()
        self.assertFalse(os.path.exists(lock_path))

    # Regression 2: Current running task should not self-block when concurrency = 1
    def test_concurrency_one_does_not_self_block(self):
        runtime = HierarchicalRuntime(work_item_id="WORK-TEST-001", state_dir=self.workspace)
        
        # Configure concurrency limit = 1 and set current task to "running"
        runtime.task_graph["concurrency_limit"] = 1
        runtime.task_graph["tasks"] = {
            "TASK-004": {
                "name": "Backend Implementation",
                "role": "subagent",
                "status": "running",
                "dependencies": [],
                "write_scope": "sources/backend/"
            }
        }
        
        # Mock psutil.virtual_memory to return low memory usage to bypass host RAM limitations
        import psutil
        original_virtual_memory = psutil.virtual_memory
        class MockVirtualMemory:
            percent = 10.0
        psutil.virtual_memory = lambda: MockVirtualMemory()
        
        try:
            # Verify that evaluating TASK-004 does NOT trigger concurrency self-blocking
            allowed, reason = runtime.can_spawn_subagent("AGENT-BACKEND-001", "TASK-004")
            self.assertTrue(allowed, f"Should be allowed to spawn because task excludes itself from running checks. Reason: {reason}")
        finally:
            psutil.virtual_memory = original_virtual_memory

    # Regression 3: kill_process_tree must correctly kill process trees recursively on timeout
    def test_coordinator_timeout_cleanup(self):
        # Spawn a dummy process tree: python shell running a child sleep process
        code = "import subprocess, time; subprocess.Popen(['sleep', '100']); time.sleep(100)"
        p = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Allow time to spawn child
        time.sleep(0.5)
        
        import psutil
        proc = psutil.Process(p.pid)
        children = proc.children(recursive=True)
        self.assertTrue(len(children) >= 1, "Should have spawned a child sleep process.")
        child_pids = [c.pid for c in children]

        # Call the new robust process tree killer
        kill_process_tree(p.pid, timeout=2.0)

        # Verify parent is dead
        self.assertFalse(p.poll() is None or proc.is_running(), "Parent process must be terminated.")
        
        # Verify children are dead
        for cpid in child_pids:
            try:
                cproc = psutil.Process(cpid)
                self.assertFalse(cproc.is_running(), f"Child process {cpid} must be terminated.")
            except psutil.NoSuchProcess:
                pass # expected

if __name__ == "__main__":
    unittest.main()
