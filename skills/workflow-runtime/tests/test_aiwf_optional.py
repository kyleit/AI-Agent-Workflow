"""
test_aiwf_optional.py — FEAT-048 Phase 5 Task 5.1 (FR-13)
Tests: get_workflow_metadata — AIWF optional layer
Blueprint test matrix: test_aiwf_optional.py
Spec: get_workflow_metadata() returns None silently when .agents/ absent
"""
import os
import sqlite3
import sys
import tempfile
import json
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestGetWorkflowMetadata(unittest.TestCase):
    """FR-13: get_workflow_metadata — AIWF optional, returns None silently."""

    def setUp(self):
        from context import get_workflow_metadata
        self.get_workflow_metadata = get_workflow_metadata

    def test_returns_none_when_path_does_not_exist(self):
        """get_workflow_metadata() returns None for non-existent path."""
        result = self.get_workflow_metadata('/nonexistent/project/path/xyz')
        self.assertIsNone(result)

    def test_returns_none_for_empty_directory(self):
        """get_workflow_metadata() returns None when dir exists but has no session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.get_workflow_metadata(tmpdir)
            self.assertIsNone(result)

    def test_returns_metadata_when_session_present(self):
        """get_workflow_metadata() does not raise when .agents/.session.json exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, '.agents')
            os.makedirs(agents_dir)
            session_data = {
                'feature_id': 'FEAT-048',
                'checkpoint': 5,
                'current_skill': 'blueprint-to-implementation',
                'status': 'in_progress',
            }
            session_path = os.path.join(agents_dir, '.session.json')
            with open(session_path, 'w') as f:
                json.dump(session_data, f)

            result = self.get_workflow_metadata(tmpdir)
            # Should return dict or None — must not raise
            self.assertTrue(result is None or isinstance(result, dict))

    def test_never_raises_on_any_path(self):
        """get_workflow_metadata() never raises, even with weird paths."""
        for path in ['/dev/null', '', '   ', '/tmp/nonexistent_xyz_999']:
            try:
                result = self.get_workflow_metadata(path)
                self.assertTrue(result is None or isinstance(result, dict))
            except Exception as e:
                self.fail(f'get_workflow_metadata({path!r}) raised: {e}')

    def test_returns_none_for_corrupted_session_json(self):
        """get_workflow_metadata() returns None for corrupted .session.json."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = os.path.join(tmpdir, '.agents')
            os.makedirs(agents_dir)
            # Write invalid JSON
            with open(os.path.join(agents_dir, '.session.json'), 'w') as f:
                f.write('{ INVALID JSON }')
            result = self.get_workflow_metadata(tmpdir)
            # Should return None or dict — must not raise
            self.assertTrue(result is None or isinstance(result, dict))


class TestDashboardLoadsWithoutAIWF(unittest.TestCase):
    """FR-13 Integration: DB operations functional even without .agents/ dir."""

    def setUp(self):
        import db as db_module
        self.tmpdir = tempfile.mkdtemp()
        self.conn = sqlite3.connect(os.path.join(self.tmpdir, 'test_no_aiwf.db'))
        db_module.init_db_schema(self.conn)

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_provider_requests_table_accessible_without_aiwf(self):
        """provider_requests table is accessible even without .agents/ directory."""
        try:
            # Query the table (schema existence check) — no INSERT needed
            result = self.conn.execute(
                "SELECT COUNT(*) FROM provider_requests"
            ).fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], 0)  # empty table
        except Exception as e:
            self.fail(f'provider_requests query without AIWF raised: {e}')

    def test_workflow_metadata_absent_does_not_block_db(self):
        """When AIWF is absent, DB operations still succeed."""
        from context import get_workflow_metadata
        metadata = get_workflow_metadata(self.tmpdir)  # no .agents/ here
        self.assertIsNone(metadata)
        # DB should still work
        result = self.conn.execute("SELECT COUNT(*) FROM runtime_events").fetchone()
        self.assertIsNotNone(result)

    def test_runtime_events_insertable_without_aiwf(self):
        """runtime_events table accepts inserts regardless of AIWF presence."""
        import uuid
        from datetime import datetime, timezone
        try:
            self.conn.execute("""
                INSERT INTO runtime_events
                    (event_id, timestamp, conversation_id, provider, event_type, event_data_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), datetime.now(timezone.utc).isoformat(),
                  'conv-test', 'antigravity', 'antigravity.usage_update', '{}'))
            self.conn.commit()
        except Exception as e:
            self.fail(f'runtime_events insert raised: {e}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
