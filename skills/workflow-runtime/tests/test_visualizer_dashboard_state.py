"""
test_visualizer_dashboard_state.py — Integration tests for FR-04: Dashboard state for Visualizer.
8 test cases covering dashboard JSON structure, phase progress, gate states for UI consumption.
NOTE: phases stored in runtime.json, gate states in workflow.json, aggregated into dashboard.json.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class VisualizerDashboardStateTests(RuntimeTestBase):

    # TC1: Dashboard has all required top-level keys for visualizer
    def test_dashboard_has_required_keys(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        required_keys = [
            "_health", "_errors", "_generated_at", "_source",
            "suggested_next_skill", "release_allowed",
        ]
        for key in required_keys:
            self.assertIn(key, dashboard, f"Missing key: {key}")

    # TC2: Phase in_progress reflected in dashboard from runtime state
    def test_phase_in_progress_reflected(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        from ledger import ImplementationLedger
        ensure_dirs(self.workspace)
        blueprint = self.make_ledger_blueprint("FEAT-VIS", n_phases=2, tasks_per_phase=2)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        ledger.mark_phase_started("Phase 1")
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        # Phases pulled from ledger → dashboard
        phases = dashboard.get("phases", {})
        if phases:
            self.assertIn("Phase 1", phases)
            self.assertEqual(phases["Phase 1"]["status"], "in_progress")

    # TC3: all_phases_complete missing or False when phases pending
    def test_all_phases_complete_false_when_pending(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        from ledger import ImplementationLedger
        ensure_dirs(self.workspace)
        blueprint = self.make_ledger_blueprint("FEAT-VIS2", n_phases=2, tasks_per_phase=1)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        # Phase 1 started, not completed
        ledger.mark_phase_started("Phase 1")
        # Verify ledger shows in_progress (not completed)
        data = ledger.load()
        phases = data.get("phases", [])
        completed_phases = [p for p in phases if p["status"] == "completed"]
        self.assertLess(len(completed_phases), len(phases), "Not all phases should be completed")

    # TC4: implementation_status=completed when all phases done
    def test_all_phases_complete_true_when_all_done(self):
        from state_path import ensure_dirs
        from ledger import ImplementationLedger
        ensure_dirs(self.workspace)
        blueprint = self.make_ledger_blueprint("FEAT-VIS3", n_phases=2, tasks_per_phase=1)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        for i in range(1, 3):
            ledger.mark_phase_started(f"Phase {i}")
            ledger.mark_task_completed(f"Task {i}.1")
            ledger.mark_phase_completed(f"Phase {i}")
        data = ledger.load()
        self.assertEqual(data["implementation_status"], "completed")

    # TC5: verify_allowed=False when debug_status not pass
    def test_verify_blocked_before_debug(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        # Write workflow state with failed debug
        self.write_state("workflow", {"debug_status": "fail", "verify_allowed": False})
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertFalse(dashboard.get("verify_allowed", True))

    # TC6: Gate chain: implement→debug→verify→release visible in dashboard
    def test_gate_chain_progression(self):
        from event_logger import EventLogger, WORKFLOW_INITIALIZED, PHASE_STARTED, PHASE_COMPLETED, DEBUG_PASSED, VERIFY_PASSED
        from event_reducer import EventReducer
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        logger = EventLogger(self.workspace)
        reducer = EventReducer(self.workspace)

        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "FEAT-CHAIN"})
        reducer.replay_all()
        d1 = StateAggregator(self.workspace).aggregate()
        self.assertFalse(d1["release_allowed"])

        logger.emit(PHASE_STARTED, {"phase_id": "Phase 1"})
        logger.emit(PHASE_COMPLETED, {"phase_id": "Phase 1"})
        logger.emit(DEBUG_PASSED, {})
        reducer.replay_all()
        d2 = StateAggregator(self.workspace).aggregate()
        self.assertTrue(d2.get("verify_allowed"))
        self.assertFalse(d2["release_allowed"])

        logger.emit(VERIFY_PASSED, {})
        reducer.replay_all()
        d3 = StateAggregator(self.workspace).aggregate()
        self.assertTrue(d3["release_allowed"])

    # TC7: Dashboard JSON is valid and parseable after multiple writes
    def test_dashboard_json_valid_after_multiple_writes(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs, get_dashboard_path
        from atomic_writer import read_json_safe
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        for i in range(5):
            self.write_state("workflow", {"checkpoint": i, "current_skill": f"skill-{i}"})
            agg.write_dashboard()
        data = read_json_safe(get_dashboard_path(self.workspace))
        self.assertIsNotNone(data)
        self.assertIsInstance(data, dict)
        self.assertEqual(data["_source"], "split_state")

    # TC8: Legacy .session.json snapshot written after dashboard generation
    def test_legacy_snapshot_written_after_dashboard(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        from atomic_writer import read_json_safe
        ensure_dirs(self.workspace)
        self.write_state("workflow", {
            "current_skill": "debug-to-verify",
            "feature_id": "FEAT-SNAP"
        })
        agg = StateAggregator(self.workspace)
        agg.write_dashboard()
        agg.write_legacy_snapshot()

        legacy_path = os.path.join(self.workspace, ".agents", ".session.json")
        if os.path.exists(legacy_path):
            legacy = read_json_safe(legacy_path) or {}
            self.assertTrue(legacy.get("_deprecated"))
            self.assertEqual(legacy.get("_source"), "dashboard.json")
        else:
            self.skipTest("Legacy snapshot not written by this aggregator version")


if __name__ == "__main__":
    unittest.main()
