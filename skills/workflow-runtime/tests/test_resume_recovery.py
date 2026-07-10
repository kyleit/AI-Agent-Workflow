"""
test_resume_recovery.py — Integration tests for FR-04: Resume/Recovery.
8 test cases covering checkpoint restore, partial completion recovery, state consistency.
NOTE: get_active_locks() auto-clears stale (dead PID) locks. Tests account for this.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class ResumeRecoveryTests(RuntimeTestBase):

    def _setup_partial_completion(self, n_phases=3, completed_phases=1) -> "ImplementationLedger":
        """Setup a ledger with some phases already completed."""
        from ledger import ImplementationLedger
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        blueprint = self.make_ledger_blueprint("FEAT-RECOVER", n_phases=n_phases, tasks_per_phase=2)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        for phase_n in range(1, completed_phases + 1):
            phase_id = f"Phase {phase_n}"
            ledger.mark_phase_started(phase_id)
            for task_n in range(1, 3):
                ledger.mark_task_completed(f"Task {phase_n}.{task_n}")
            ledger.mark_phase_completed(phase_id)
        return ledger

    # TC1: Resume from Phase 2 — ledger correctly identifies next incomplete phase
    def test_resume_identifies_next_phase(self):
        ledger = self._setup_partial_completion(n_phases=3, completed_phases=1)
        next_phase = ledger.get_next_incomplete_phase()
        self.assertEqual(next_phase, "Phase 2")

    # TC2: Partial task completion — failed task can be retried (re-marked completed)
    def test_failed_task_can_retry(self):
        from ledger import ImplementationLedger
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        blueprint = self.make_ledger_blueprint("FEAT-RETRY", n_phases=1, tasks_per_phase=3)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        ledger.mark_phase_started("Phase 1")
        ledger.mark_task_completed("Task 1.1")
        ledger.mark_task_failed("Task 1.2", "Build error")
        data = ledger.load()
        task = data["tasks"]["Task 1.2"]
        self.assertEqual(task["status"], "failed")
        # Retry: mark completed
        ledger.mark_task_completed("Task 1.2")
        data2 = ledger.load()
        self.assertEqual(data2["tasks"]["Task 1.2"]["status"], "completed")

    # TC3: Stale locks (dead PID) are auto-cleared when re-acquiring
    def test_stale_locks_cleared_on_resume(self):
        from lock_manager import LockManager
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        lm = LockManager(self.workspace)
        # Acquire with dead PID — lock stored in file
        lm.acquire("Task 1.1", ["src/a.py", "src/b.py"], pid=99999999)
        # get_active_locks() auto-clears stale → 0 active locks
        self.assertEqual(lm.get_lock_count(), 0)
        # Re-acquire with live PID — should succeed immediately
        ok = lm.acquire("Task 1.1-retry", ["src/a.py"], pid=os.getpid())
        self.assertTrue(ok, "Should succeed after stale locks cleared")

    # TC4: Orphan workers terminated on resume
    def test_orphan_workers_terminated_on_resume(self):
        from worker_manager import WorkerManager
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        wm = WorkerManager(self.workspace)
        wm.register("Task1", pid=99999991, command="dead1")
        wm.register("Task2", pid=99999992, command="dead2")
        wm.register("Task3", pid=os.getpid(), command="alive")

        orphans = wm.detect_orphans()
        for oid in orphans:
            wm.terminate_orphan(oid)

        active = wm.get_active_workers()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["task_id"], "Task3")

    # TC5: Event log replay after crash — state reconstructed correctly
    def test_event_log_replay_after_crash(self):
        from event_logger import EventLogger, WORKFLOW_INITIALIZED, PHASE_STARTED, PHASE_COMPLETED, DEBUG_PASSED
        from event_reducer import EventReducer
        from state_path import ensure_dirs, get_state_file
        from atomic_writer import read_json_safe
        ensure_dirs(self.workspace)

        logger = EventLogger(self.workspace)
        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "FEAT-CRASH"})
        logger.emit(PHASE_STARTED, {"phase_id": "Phase 1"})
        logger.emit(PHASE_COMPLETED, {"phase_id": "Phase 1"})
        logger.emit(DEBUG_PASSED, {})

        # Simulate crash: delete workflow state file
        state_file = get_state_file("workflow", self.workspace)
        if os.path.exists(state_file):
            os.remove(state_file)

        # Replay from event log to recover
        reducer = EventReducer(self.workspace)
        reducer.replay_all()

        # debug_status should be recovered in workflow state
        workflow = read_json_safe(state_file) or {}
        self.assertEqual(workflow.get("debug_status"), "pass")

        # phases in runtime state
        runtime_file = get_state_file("runtime", self.workspace)
        runtime = read_json_safe(runtime_file) or {}
        phases = runtime.get("phases", {})
        self.assertIn("Phase 1", phases)
        self.assertEqual(phases["Phase 1"]["status"], "completed")

    # TC6: Dashboard reflects partial completion correctly
    def test_dashboard_shows_partial_completion(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        self._setup_partial_completion(n_phases=3, completed_phases=2)
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        # 3 phases, only 2 complete → not fully done → release not allowed
        self.assertFalse(dashboard["release_allowed"])

    # TC7: is_stale correctly identifies dead PID lock entries (raw data check)
    def test_detect_stale_pid_in_lock_file(self):
        from lock_manager import LockManager
        from state_path import ensure_dirs
        from atomic_writer import read_json_safe
        ensure_dirs(self.workspace)
        lm = LockManager(self.workspace)
        lm.acquire("StaleTask", ["src/stale.py"], pid=99999999)

        # Read raw file to check lock is stored
        raw = read_json_safe(lm._path) or {}
        locks = raw.get("locks", {})
        self.assertIn("src/stale.py", locks)

        # Verify is_stale returns True for dead PID
        lock_entry = locks["src/stale.py"]
        self.assertTrue(lm.is_stale(lock_entry))

    # TC8: After full recovery from crashed phase, re-run succeeds cleanly
    def test_full_recovery_reruns_cleanly(self):
        from ledger import ImplementationLedger
        from lock_manager import LockManager
        from worker_manager import WorkerManager
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)

        blueprint = self.make_ledger_blueprint("FEAT-CLEAN", n_phases=1, tasks_per_phase=2)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        ledger.mark_phase_started("Phase 1")
        ledger.mark_task_completed("Task 1.1")

        # Simulate stale lock + dead worker for Task 1.2
        lm = LockManager(self.workspace)
        wm = WorkerManager(self.workspace)
        lm.acquire("Task 1.2", ["src/b.py"], pid=99999999)
        wm.register("Task 1.2", pid=99999999, command="crashed")

        # Recovery: clear orphans, re-acquire
        for orphan in wm.detect_orphans():
            wm.terminate_orphan(orphan)
        # Stale lock auto-cleared by acquire
        ok = lm.acquire("Task 1.2", ["src/b.py"], pid=os.getpid())
        self.assertTrue(ok)
        lm.release("Task 1.2")
        ledger.mark_task_completed("Task 1.2")
        ledger.mark_phase_completed("Phase 1")

        data = ledger.load()
        self.assertEqual(data["implementation_status"], "completed")
        self.assertEqual(lm.get_lock_count(), 0)


if __name__ == "__main__":
    unittest.main()
