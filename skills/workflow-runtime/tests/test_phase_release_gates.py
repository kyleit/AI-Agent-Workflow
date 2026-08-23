"""
test_phase_release_gates.py — Tests for FEAT-051 phase lifecycle and release gate.
8 test cases covering gate conditions, confirmation, partial release.
"""
import os
import sys
import json
import unittest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class PhaseReleaseGateTests(RuntimeTestBase):

    def _setup_ledger(self, feature_id="FEAT-TEST", phases=1) -> "ImplementationLedger":
        from ledger import ImplementationLedger
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        ledger = ImplementationLedger(self.workspace)
        blueprint = self.make_ledger_blueprint(feature_id, n_phases=phases, tasks_per_phase=1)
        ledger.init_from_blueprint(blueprint)
        return ledger

    # TC1: Phase 1 complete, Phase 2 pending → release blocked, continue implement
    def test_phase1_complete_phase2_pending_blocks_release(self):
        from phase_controller import PhaseController
        from release_gate import ReleaseGate
        from ledger import ImplementationLedger

        ledger = self._setup_ledger(phases=2)
        ledger.mark_phase_started("Phase 1")
        ledger.mark_task_completed("Task 1.1")
        ledger.mark_phase_completed("Phase 1")

        pc = PhaseController(self.workspace)
        result = pc.on_phase_completed("Phase 1")

        self.assertEqual(result["next_action"], "continue_implement")
        self.assertEqual(result["next_phase_id"], "Phase 2")
        self.assertFalse(result["release_allowed"])

        # Release gate must also block
        gate = ReleaseGate(self.workspace)
        allowed, reason = gate.validate()
        self.assertFalse(allowed)
        self.assertIn("Phase 2", reason)

    # TC2: All phases complete → next_action = debug, release still needs debug/verify
    def test_all_phases_complete_needs_debug(self):
        from phase_controller import PhaseController
        from release_gate import ReleaseGate
        from ledger import ImplementationLedger

        ledger = self._setup_ledger(phases=1)
        ledger.mark_phase_started("Phase 1")
        ledger.mark_task_completed("Task 1.1")
        ledger.mark_phase_completed("Phase 1")

        pc = PhaseController(self.workspace)
        result = pc.on_phase_completed("Phase 1")
        self.assertEqual(result["next_action"], "debug")
        self.assertIsNone(result["next_phase_id"])

        # Release gate blocks because no debug/verify reports
        gate = ReleaseGate(self.workspace)
        allowed, reason = gate.validate()
        self.assertFalse(allowed)

    # TC3: Debug PASS → verify_allowed=True in aggregator
    def test_debug_pass_allows_verify(self):
        from event_logger import EventLogger, DEBUG_PASSED, WORKFLOW_INITIALIZED
        from event_reducer import EventReducer
        from state_path import ensure_dirs

        ensure_dirs(self.workspace)
        logger = EventLogger(self.workspace)
        reducer = EventReducer(self.workspace)

        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "FEAT-TEST"})
        eid = logger.emit(DEBUG_PASSED, {"feature_id": "FEAT-TEST"})
        reducer.replay_all()

        from state_path import get_state_file
        from atomic_writer import read_json_safe
        workflow = read_json_safe(get_state_file("workflow", self.workspace)) or {}
        self.assertEqual(workflow.get("debug_status"), "pass")
        self.assertTrue(workflow.get("verify_allowed"))

    # TC4: Verify PASS → release_allowed=True in workflow state
    def test_verify_pass_allows_release(self):
        from event_logger import EventLogger, VERIFY_PASSED, WORKFLOW_INITIALIZED
        from event_reducer import EventReducer
        from state_path import ensure_dirs, get_state_file
        from atomic_writer import read_json_safe

        ensure_dirs(self.workspace)
        logger = EventLogger(self.workspace)
        reducer = EventReducer(self.workspace)

        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "FEAT-TEST"})
        logger.emit(VERIFY_PASSED, {"feature_id": "FEAT-TEST"})
        reducer.replay_all()

        workflow = read_json_safe(get_state_file("workflow", self.workspace)) or {}
        self.assertEqual(workflow.get("verify_status"), "pass")
        self.assertTrue(workflow.get("release_allowed"))

    # TC5: Debug FAILED → verify_allowed=False
    def test_debug_failed_blocks_verify(self):
        from event_logger import EventLogger, DEBUG_FAILED, WORKFLOW_INITIALIZED
        from event_reducer import EventReducer
        from state_path import ensure_dirs, get_state_file
        from atomic_writer import read_json_safe

        ensure_dirs(self.workspace)
        logger = EventLogger(self.workspace)
        reducer = EventReducer(self.workspace)

        logger.emit(WORKFLOW_INITIALIZED, {})
        logger.emit(DEBUG_FAILED, {"reason": "test failures"})
        reducer.replay_all()

        workflow = read_json_safe(get_state_file("workflow", self.workspace)) or {}
        self.assertFalse(workflow.get("verify_allowed", False))
        self.assertFalse(workflow.get("release_allowed", False))

    # TC6: Partial release requires exact confirmation
    def test_partial_release_confirmation_exact_match(self):
        from release_gate import ReleaseGate, PartialReleaseConfirmationError

        gate = ReleaseGate(self.workspace)

        # Exact match passes
        result = gate.require_explicit_confirmation("Approve partial release for Phase 1", "Phase 1")
        self.assertTrue(result)

        # Wrong text raises error
        with self.assertRaises(PartialReleaseConfirmationError):
            gate.require_explicit_confirmation("approve phase 1", "Phase 1")

        # Wrong phase raises error
        with self.assertRaises(PartialReleaseConfirmationError):
            gate.require_explicit_confirmation("Approve partial release for Phase 2", "Phase 1")

    # TC7: Release gate missing ledger → blocks with clear message
    def test_release_gate_no_ledger_blocks(self):
        from release_gate import ReleaseGate

        gate = ReleaseGate(self.workspace)
        allowed, reason = gate.validate()
        self.assertFalse(allowed)
        self.assertIn("ledger", reason.lower())

    # TC8: Release gate validates implementation_status = 'completed'
    def test_release_gate_requires_impl_completed(self):
        from release_gate import ReleaseGate
        from ledger import ImplementationLedger
        from state_path import ensure_dirs

        ensure_dirs(self.workspace)
        ledger = self._setup_ledger(phases=1)
        # Phase NOT completed → implementation_status = 'not_started'
        gate = ReleaseGate(self.workspace)
        allowed, reason = gate.validate()
        self.assertFalse(allowed)
        # Block reason should mention incomplete phases or implementation status
        self.assertGreater(len(reason), 0)


if __name__ == "__main__":
    unittest.main()
