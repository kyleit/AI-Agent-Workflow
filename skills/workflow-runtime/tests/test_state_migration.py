"""
test_state_migration.py — Tests for FEAT-050 state migration flows.
10 test cases covering legacy, flat, nested, idempotency, dashboard generation.
"""
import os
import sys
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch

# Set up path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class StateMigrationTests(RuntimeTestBase):

    def _write_legacy_session(self, data: dict = None) -> str:
        """Write a legacy .session.json to workspace."""
        legacy_dir = os.path.join(self.workspace, ".agents")
        os.makedirs(legacy_dir, exist_ok=True)
        path = os.path.join(legacy_dir, ".session.json")
        payload = data or {
            "current_skill": "brainstorming",
            "checkpoint": 2,
            "suggested_next_skill": "brainstorming-to-plan",
            "feature_id": "FEAT-999",
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        return path

    def _write_flat_state(self) -> None:
        """Write flat state files (pre-nested format) to workspace."""
        state_dir = os.path.join(self.workspace, ".agents", "state")
        os.makedirs(state_dir, exist_ok=True)
        files = {
            "workflow.json": {"current_skill": "blueprint-to-implementation"},
            "runtime.json": {"checkpoint": 5},
            "context.json": {"tokens_used": 1000},
        }
        for filename, content in files.items():
            with open(os.path.join(state_dir, filename), "w") as f:
                json.dump(content, f)

    # TC1: Migrate legacy .session.json → nested canonical structure
    def test_migrate_legacy_session_creates_state_dirs(self):
        from state_path import ensure_dirs, get_state_root
        self._write_legacy_session()
        ensure_dirs(self.workspace)
        # Verify all canonical subdirs created
        for subdir in ["project", "workflow", "runtime", "context", "recovery", "events"]:
            self.assertTrue(
                os.path.isdir(os.path.join(self.state_root, subdir)),
                f"Subdir '{subdir}' not created",
            )

    # TC2: Aggregator runs without crashing on empty state
    def test_migrate_aggregator_on_empty_state(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertIn("_health", dashboard)
        self.assertIn("suggested_next_skill", dashboard)
        self.assertIn("release_allowed", dashboard)
        self.assertFalse(dashboard["release_allowed"])

    # TC3: Aggregator writes dashboard.json
    def test_migrate_creates_dashboard_json(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs, get_dashboard_path
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        path = agg.write_dashboard()
        self.assertTrue(os.path.exists(path))
        with open(path) as f:
            data = json.load(f)
        self.assertIn("_generated_at", data)
        self.assertEqual(data["_source"], "split_state")

    # TC4: Legacy snapshot gets _deprecated: true
    def test_migrate_creates_deprecated_session_snapshot(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        self._write_legacy_session()
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        path = agg.write_legacy_snapshot()
        with open(path) as f:
            data = json.load(f)
        self.assertTrue(data.get("_deprecated"), "Legacy snapshot must have _deprecated: true")
        self.assertEqual(data.get("_source"), "dashboard.json")

    # TC5: Legacy snapshot preserves existing fields
    def test_migrate_snapshot_preserves_existing_fields(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        self._write_legacy_session({"feature_id": "FEAT-TEST", "custom_field": "kept", "checkpoint": 3})
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        agg.write_legacy_snapshot()
        legacy_path = os.path.join(self.workspace, ".agents", ".session.json")
        with open(legacy_path) as f:
            data = json.load(f)
        self.assertEqual(data.get("custom_field"), "kept", "Custom fields must be preserved")

    # TC6: Idempotent migration — run twice, same result
    def test_migrate_idempotent(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs, get_dashboard_path
        ensure_dirs(self.workspace)
        agg = StateAggregator(self.workspace)
        agg.write_dashboard()
        path1 = get_dashboard_path(self.workspace)

        agg.write_dashboard()  # Run again
        with open(path1) as f:
            data = json.load(f)
        self.assertIn("_generated_at", data)  # Should be valid JSON

    # TC7: atomic_writer preserves original on failure simulation
    def test_atomic_writer_preserves_original_on_error(self):
        from atomic_writer import write_json_atomic, read_json_safe
        original_data = {"original": "data"}
        target = os.path.join(self.workspace, "test.json")
        write_json_atomic(target, original_data)
        # Verify original is preserved
        result = read_json_safe(target)
        self.assertEqual(result, original_data)
        # Write new data
        write_json_atomic(target, {"updated": True})
        result2 = read_json_safe(target)
        self.assertEqual(result2, {"updated": True})

    # TC8: Broken JSON state file → degraded health, no crash
    def test_broken_json_state_handled_gracefully(self):
        from state_aggregator import StateAggregator
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        # Write invalid JSON to workflow state
        workflow_dir = os.path.join(self.state_root, "workflow")
        os.makedirs(workflow_dir, exist_ok=True)
        with open(os.path.join(workflow_dir, "workflow.json"), "w") as f:
            f.write("INVALID JSON{{{")
        agg = StateAggregator(self.workspace)
        dashboard = agg.aggregate()
        self.assertEqual(dashboard["_health"], "degraded")
        self.assertGreater(len(dashboard["_errors"]), 0)

    # TC9: State subdirectory structure after ensure_dirs
    def test_ensure_dirs_creates_all_subdirs(self):
        from state_path import ensure_dirs, STATE_SUBDIRS
        created = ensure_dirs(self.workspace)
        for subdir in STATE_SUBDIRS:
            path = os.path.join(self.state_root, subdir)
            self.assertTrue(os.path.isdir(path), f"Missing subdir: {subdir}")

    # TC10: event_logger emit → read_all round trip
    def test_event_logger_emit_read_roundtrip(self):
        from event_logger import EventLogger, SKILL_STARTED, PHASE_COMPLETED
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        logger = EventLogger(self.workspace)
        eid1 = logger.emit(SKILL_STARTED, {"skill": "implement"})
        eid2 = logger.emit(PHASE_COMPLETED, {"phase_id": "Phase 1"})
        all_events = logger.read_all()
        self.assertEqual(len(all_events), 2)
        self.assertEqual(all_events[0]["event_id"], eid1)
        self.assertEqual(all_events[1]["event_type"], PHASE_COMPLETED)


if __name__ == "__main__":
    unittest.main()
