"""
test_worker_registry.py — Tests for FEAT-052 WorkerManager (workers.json).
10 test cases covering register, complete, orphan detection, terminate.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class WorkerRegistryTests(RuntimeTestBase):

    def _make_wm(self):
        from worker_manager import WorkerManager
        return WorkerManager(self.workspace)

    # TC1: Register worker → appears in active list
    def test_register_worker_appears_active(self):
        wm = self._make_wm()
        wid = wm.register("Task1.1", pid=os.getpid(), command="python build.py")
        self.assertIsNotNone(wid)
        active = wm.get_active_workers()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["worker_id"], wid)
        self.assertEqual(active[0]["status"], "running")

    # TC2: mark_completed removes from active
    def test_mark_completed_removes_from_active(self):
        wm = self._make_wm()
        wid = wm.register("Task1.1", pid=os.getpid(), command="test")
        self.assertTrue(wm.has_active_workers())
        wm.mark_completed(wid)
        self.assertFalse(wm.has_active_workers())

    # TC3: mark_failed records error
    def test_mark_failed_records_error(self):
        wm = self._make_wm()
        wid = wm.register("Task1.1", pid=os.getpid(), command="test")
        wm.mark_failed(wid, "Build error: exit code 1")
        worker = wm.get_worker(wid)
        self.assertEqual(worker["status"], "failed")
        self.assertIn("Build error", worker["error"])

    # TC4: detect_orphans finds dead PIDs
    def test_detect_orphans_finds_dead_pids(self):
        wm = self._make_wm()
        wid_alive = wm.register("Task1.1", pid=os.getpid(), command="alive")
        wid_dead = wm.register("Task1.2", pid=99999999, command="dead")
        orphans = wm.detect_orphans()
        self.assertIn(wid_dead, orphans)
        self.assertNotIn(wid_alive, orphans)

    # TC5: detect_orphans skips completed workers
    def test_detect_orphans_skips_completed(self):
        wm = self._make_wm()
        wid = wm.register("Task1.1", pid=99999999, command="test")
        wm.mark_completed(wid)
        orphans = wm.detect_orphans()
        self.assertNotIn(wid, orphans)

    # TC6: terminate_orphan marks as orphaned
    def test_terminate_orphan_marks_status(self):
        wm = self._make_wm()
        wid = wm.register("Task1.1", pid=99999999, command="dead")
        result = wm.terminate_orphan(wid)
        self.assertTrue(result)
        worker = wm.get_worker(wid)
        self.assertEqual(worker["status"], "orphaned")

    # TC7: get_workers_for_task returns correct workers
    def test_get_workers_for_task(self):
        wm = self._make_wm()
        wid1 = wm.register("Task1.1", pid=os.getpid(), command="a")
        wid2 = wm.register("Task1.2", pid=os.getpid(), command="b")
        workers_t1 = wm.get_workers_for_task("Task1.1")
        self.assertEqual(len(workers_t1), 1)
        self.assertEqual(workers_t1[0]["worker_id"], wid1)

    # TC8: log_file path is set on registration
    def test_log_file_path_set_on_register(self):
        wm = self._make_wm()
        wid = wm.register("Task1.1", pid=os.getpid(), command="test")
        worker = wm.get_worker(wid)
        self.assertIn("log_file", worker)
        self.assertIn(wid, worker["log_file"])

    # TC9: cleanup_completed removes completed but keeps failed
    def test_cleanup_completed_keeps_failed(self):
        wm = self._make_wm()
        wid_ok = wm.register("Task1.1", pid=os.getpid(), command="ok")
        wid_fail = wm.register("Task1.2", pid=os.getpid(), command="fail")
        wm.mark_completed(wid_ok)
        wm.mark_failed(wid_fail, "error")
        removed = wm.cleanup_completed(keep_failed=True)
        self.assertEqual(removed, 1)  # Only completed removed
        self.assertIsNotNone(wm.get_worker(wid_fail))

    # TC10: has_active_workers is False when all completed
    def test_has_active_workers_false_when_done(self):
        wm = self._make_wm()
        self.assertFalse(wm.has_active_workers())
        wid = wm.register("Task1.1", pid=os.getpid(), command="test")
        self.assertTrue(wm.has_active_workers())
        wm.mark_completed(wid)
        self.assertFalse(wm.has_active_workers())


if __name__ == "__main__":
    unittest.main()
