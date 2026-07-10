"""
test_file_locks.py — Tests for FEAT-052 LockManager (file-locks.json).
10 test cases covering all-or-nothing acquisition, stale detection, security.
"""
import os
import sys
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class LockManagerTests(RuntimeTestBase):

    def _make_lm(self):
        from lock_manager import LockManager
        return LockManager(self.workspace)

    # TC1: Basic acquire and release
    def test_acquire_and_release(self):
        lm = self._make_lm()
        result = lm.acquire("Task1.1", ["src/a.py", "src/b.py"], pid=os.getpid())
        self.assertTrue(result)
        active = lm.get_active_locks()
        self.assertEqual(len(active), 2)

        released = lm.release("Task1.1")
        self.assertIn("src/a.py", released)
        self.assertEqual(len(lm.get_active_locks()), 0)

    # TC2: All-or-nothing — partial lock not left on conflict
    def test_all_or_nothing_no_partial_lock(self):
        lm = self._make_lm()
        # Acquire first lock on src/a.py
        lm.acquire("Task1.1", ["src/a.py"], pid=os.getpid())
        # Try to acquire on src/a.py + src/b.py → should fail entirely
        result = lm.acquire("Task1.2", ["src/a.py", "src/b.py"], pid=os.getpid())
        self.assertFalse(result)
        # src/b.py should NOT be locked (all-or-nothing)
        active = {lock["file_path"]: lock for lock in lm.get_active_locks()}
        self.assertNotIn("src/b.py", active)
        # Only Task1.1's lock on src/a.py should exist
        self.assertIn("src/a.py", active)
        self.assertEqual(active["src/a.py"]["task_id"], "Task1.1")

    # TC3: Absolute path raises SecurityError
    def test_absolute_path_raises_security_error(self):
        from state_path import SecurityError
        lm = self._make_lm()
        with self.assertRaises(SecurityError):
            lm.acquire("TaskX", ["/etc/hosts"], pid=os.getpid())

    # TC4: Path traversal raises SecurityError
    def test_path_traversal_raises_security_error(self):
        from state_path import SecurityError
        lm = self._make_lm()
        with self.assertRaises(SecurityError):
            lm.acquire("TaskX", ["../outside/secret.txt"], pid=os.getpid())

    # TC5: Stale lock (dead PID) auto-cleared
    def test_stale_lock_cleared_before_acquire(self):
        lm = self._make_lm()
        # Acquire with dead PID (99999999 is unlikely to exist)
        result1 = lm.acquire("TaskStale", ["src/stale.py"], pid=99999999)
        self.assertTrue(result1)
        # Now try to acquire same file — should succeed because stale lock cleared
        result2 = lm.acquire("Task1.2", ["src/stale.py"], pid=os.getpid())
        self.assertTrue(result2, "Lock with dead PID should be treated as stale and cleared")

    # TC6: Empty write_set acquires successfully (no-op)
    def test_empty_write_set_succeeds(self):
        lm = self._make_lm()
        result = lm.acquire("TaskEmpty", [], pid=os.getpid())
        self.assertTrue(result)

    # TC7: has_conflict correctly detects conflicts
    def test_has_conflict_detection(self):
        lm = self._make_lm()
        lm.acquire("Task1.1", ["src/a.py"], pid=os.getpid())
        self.assertTrue(lm.has_conflict(["src/a.py"]))
        self.assertFalse(lm.has_conflict(["src/b.py"]))

    # TC8: Release only removes own locks
    def test_release_does_not_affect_other_tasks(self):
        lm = self._make_lm()
        lm.acquire("Task1.1", ["src/a.py"], pid=os.getpid())
        lm.acquire("Task1.2", ["src/b.py"], pid=os.getpid())
        lm.release("Task1.1")
        active = {lock["file_path"]: lock for lock in lm.get_active_locks()}
        self.assertNotIn("src/a.py", active)
        self.assertIn("src/b.py", active)

    # TC9: get_lock_count
    def test_lock_count(self):
        lm = self._make_lm()
        self.assertEqual(lm.get_lock_count(), 0)
        lm.acquire("T1", ["a.py"], pid=os.getpid())
        lm.acquire("T2", ["b.py"], pid=os.getpid())
        self.assertEqual(lm.get_lock_count(), 2)

    # TC10: is_stale returns True for dead PID
    def test_is_stale_dead_pid(self):
        lm = self._make_lm()
        entry = {"task_id": "T1", "pid": 99999999, "expires_at": "2099-01-01T00:00:00+00:00"}
        self.assertTrue(lm.is_stale(entry))

        # Live PID (current process) should not be stale
        entry_live = {"task_id": "T1", "pid": os.getpid(), "expires_at": "2099-01-01T00:00:00+00:00"}
        self.assertFalse(lm.is_stale(entry_live))


if __name__ == "__main__":
    unittest.main()
