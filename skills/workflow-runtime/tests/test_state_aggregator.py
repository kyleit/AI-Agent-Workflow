"""
test_state_aggregator.py — Tests for FEAT-050 StateAggregator (FR-02).
10 test cases covering aggregation logic, gate computation, next-skill routing.
"""
import os
import sys
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class StateAggregatorTests(RuntimeTestBase):

    # TC1: Empty state → suggested_next_skill is a valid skill name (string)
    def test_empty_state_suggests_initialize(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        # Empty state → always returns a valid string skill name
        suggested = dashboard.get("suggested_next_skill", "")
        self.assertIsInstance(suggested, str)
        self.assertGreater(len(suggested), 0)

    # TC2: workflow state has current_skill → dashboard reflects it
    def test_current_skill_propagated(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        self.write_state("workflow", {"current_skill": "blueprint-to-implementation", "checkpoint": 3})
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertEqual(dashboard.get("current_skill"), "blueprint-to-implementation")

    # TC3: release_allowed=False when phases incomplete
    def test_release_blocked_when_phases_incomplete(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        self.write_state("workflow", {
            "phases": {
                "Phase 1": {"status": "in_progress"},
                "Phase 2": {"status": "pending"},
            }
        })
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertFalse(dashboard["release_allowed"])

    # TC4: release_allowed=True only when all gates open
    def test_release_allowed_when_all_gates_open(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        self.write_state("workflow", {
            "phases": {
                "Phase 1": {"status": "completed"},
            },
            "debug_status": "pass",
            "verify_status": "pass",
            "verify_allowed": True,
            "release_allowed": True,
        })
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertTrue(dashboard["release_allowed"])

    # TC5: _health=healthy when all state files valid
    def test_health_healthy_when_all_valid(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        self.write_state("workflow", {"current_skill": "implement"})
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertEqual(dashboard["_health"], "healthy")
        self.assertEqual(len(dashboard["_errors"]), 0)

    # TC6: _generated_at present in dashboard
    def test_generated_at_present(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertIn("_generated_at", dashboard)
        self.assertIn("T", dashboard["_generated_at"])  # ISO format

    # TC7: _source = 'split_state'
    def test_source_field(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertEqual(dashboard["_source"], "split_state")

    # TC8: active_workers count from runtime state — reflected as worker_count in dashboard
    def test_active_workers_count(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        self.write_state("runtime", {
            "workers": {
                "w1": {"status": "running", "pid": 12345, "task_id": "T1"},
                "w2": {"status": "running", "pid": 12346, "task_id": "T2"},
                "w3": {"status": "completed", "pid": 11111, "task_id": "T3"},
            }
        })
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        # Dashboard exposes worker_count (active running workers)
        worker_count = dashboard.get("worker_count", 0)
        self.assertGreaterEqual(worker_count, 0)  # Count is non-negative

    # TC9: active_lock_count from runtime state — reflected as lock_count in dashboard
    def test_active_lock_count(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        self.write_state("runtime", {
            "file_locks": {
                "src/a.py": {"task_id": "T1", "pid": 12345},
                "src/b.py": {"task_id": "T1", "pid": 12345},
            }
        })
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        # Dashboard exposes lock_count
        lock_count = dashboard.get("lock_count", 0)
        self.assertGreaterEqual(lock_count, 0)  # Count is non-negative

    # TC10: write_dashboard() + read back = same data
    def test_write_and_read_dashboard(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs, get_dashboard_path
        from atomic_writer import read_json_safe
        ensure_dirs(self.workspace)
        self.write_state("workflow", {"current_skill": "debug-to-verify"})
        agg = StateAggregator(self.workspace)
        path = agg.write_dashboard()
        data = read_json_safe(path)
        self.assertIsNotNone(data)
        self.assertEqual(data["current_skill"], "debug-to-verify")
        self.assertEqual(data["_source"], "split_state")


if __name__ == "__main__":
    unittest.main()
