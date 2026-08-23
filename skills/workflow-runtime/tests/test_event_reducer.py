"""
test_event_reducer.py — Tests for FEAT-050 EventReducer (FR-02).
10 test cases covering all event dispatch handlers and idempotency.
NOTE: phases/tasks are stored in runtime.json, not workflow.json.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class EventReducerTests(RuntimeTestBase):

    def _read_runtime(self) -> dict:
        from atomic_writer import read_json_safe
        from state_path import get_state_file
        return read_json_safe(get_state_file("runtime", self.workspace)) or {}

    def _read_workflow(self) -> dict:
        from atomic_writer import read_json_safe
        from state_path import get_state_file
        return read_json_safe(get_state_file("workflow", self.workspace)) or {}

    def _setup(self):
        from event_logger import EventLogger
        from event_reducer import EventReducer
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        return EventLogger(self.workspace), EventReducer(self.workspace)

    # TC1: WORKFLOW_INITIALIZED sets feature_id in workflow.json
    def test_workflow_initialized(self):
        from event_logger import WORKFLOW_INITIALIZED
        logger, reducer = self._setup()
        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "FEAT-TEST", "skill": "brainstorming"})
        reducer.replay_all()
        workflow = self._read_workflow()
        self.assertEqual(workflow.get("feature_id"), "FEAT-TEST")

    # TC2: SKILL_STARTED sets current_skill in workflow.json
    def test_skill_started(self):
        from event_logger import WORKFLOW_INITIALIZED, SKILL_STARTED
        logger, reducer = self._setup()
        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "F"})
        logger.emit(SKILL_STARTED, {"skill": "plan-to-blueprint", "checkpoint": 1})
        reducer.replay_all()
        workflow = self._read_workflow()
        self.assertEqual(workflow.get("current_skill"), "plan-to-blueprint")
        self.assertEqual(workflow.get("checkpoint"), 1)

    # TC3: PHASE_COMPLETED updates phase status in runtime.json
    def test_phase_completed(self):
        from event_logger import PHASE_STARTED, PHASE_COMPLETED
        logger, reducer = self._setup()
        logger.emit(PHASE_STARTED, {"phase_id": "Phase 1"})
        logger.emit(PHASE_COMPLETED, {"phase_id": "Phase 1"})
        reducer.replay_all()
        runtime = self._read_runtime()
        phases = runtime.get("phases", {})
        self.assertIn("Phase 1", phases)
        self.assertEqual(phases["Phase 1"]["status"], "completed")

    # TC4: DEBUG_PASSED sets debug_status=pass + verify_allowed=True in workflow.json
    def test_debug_passed(self):
        from event_logger import DEBUG_PASSED
        logger, reducer = self._setup()
        logger.emit(DEBUG_PASSED, {"feature_id": "FEAT-TEST"})
        reducer.replay_all()
        workflow = self._read_workflow()
        self.assertEqual(workflow.get("debug_status"), "pass")
        self.assertTrue(workflow.get("verify_allowed"))

    # TC5: DEBUG_FAILED sets debug_status=fail + verify_allowed=False
    def test_debug_failed(self):
        from event_logger import DEBUG_FAILED
        logger, reducer = self._setup()
        logger.emit(DEBUG_FAILED, {"reason": "tests fail"})
        reducer.replay_all()
        workflow = self._read_workflow()
        self.assertEqual(workflow.get("debug_status"), "fail")
        self.assertFalse(workflow.get("verify_allowed", True))

    # TC6: VERIFY_PASSED sets verify_status=pass + release_allowed=True
    def test_verify_passed(self):
        from event_logger import VERIFY_PASSED
        logger, reducer = self._setup()
        logger.emit(VERIFY_PASSED, {"feature_id": "FEAT-TEST"})
        reducer.replay_all()
        workflow = self._read_workflow()
        self.assertEqual(workflow.get("verify_status"), "pass")
        self.assertTrue(workflow.get("release_allowed"))

    # TC7: VERIFY_FAILED sets verify_status=fail + release_allowed=False
    def test_verify_failed(self):
        from event_logger import VERIFY_FAILED
        logger, reducer = self._setup()
        logger.emit(VERIFY_FAILED, {"reason": "regression"})
        reducer.replay_all()
        workflow = self._read_workflow()
        self.assertEqual(workflow.get("verify_status"), "fail")
        self.assertFalse(workflow.get("release_allowed", True))

    # TC8: Idempotency — replaying same log twice = same result
    def test_replay_idempotent(self):
        from event_logger import WORKFLOW_INITIALIZED, DEBUG_PASSED
        logger, reducer = self._setup()
        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "F"})
        logger.emit(DEBUG_PASSED, {})
        reducer.replay_all()
        state1 = dict(self._read_workflow())
        reducer.replay_all()  # Replay again
        state2 = dict(self._read_workflow())
        self.assertEqual(state1.get("debug_status"), state2.get("debug_status"))
        self.assertEqual(state1.get("release_allowed"), state2.get("release_allowed"))

    # TC9: TASK_STARTED → TASK_COMPLETED sets task status in runtime.json
    def test_task_started_completed(self):
        from event_logger import TASK_STARTED, TASK_COMPLETED
        logger, reducer = self._setup()
        logger.emit(TASK_STARTED, {"task_id": "Task 1.1", "phase_id": "Phase 1"})
        logger.emit(TASK_COMPLETED, {"task_id": "Task 1.1", "phase_id": "Phase 1"})
        reducer.replay_all()
        runtime = self._read_runtime()
        tasks = runtime.get("tasks", {})
        self.assertIn("Task 1.1", tasks)
        self.assertEqual(tasks["Task 1.1"]["status"], "completed")

    # TC10: Unknown event type is skipped (no crash)
    def test_unknown_event_type_ignored(self):
        from atomic_writer import write_json_atomic, read_json_safe
        from state_path import get_events_path, ensure_dirs
        from event_reducer import EventReducer
        import uuid, datetime, json
        ensure_dirs(self.workspace)
        log_path = get_events_path(self.workspace)
        # Append a future unknown event directly to the log file
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(json.dumps({
                "event_id": str(uuid.uuid4()),
                "event_type": "UNKNOWN_FUTURE_EVENT_XYZ",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "payload": {"data": "future data"}
            }) + "\n")
        # Should not raise
        reducer = EventReducer(self.workspace)
        reducer.replay_all()
        # Workflow state remains a valid dict (not corrupted)
        from state_path import get_state_file
        state = read_json_safe(get_state_file("workflow", self.workspace))
        if state is not None:
            self.assertIsInstance(state, dict)
        else:
            pass  # No state written = also fine (no crash is the requirement)


if __name__ == "__main__":
    unittest.main()
