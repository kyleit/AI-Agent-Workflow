"""
test_db_schema.py — FEAT-048 Phase 5 Task 5.1
Tests: DB schema migration — new tables, columns, indexes (FR-06, FR-07, NFR-06)
Blueprint test matrix: test_db_schema.py
"""
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def make_schema_conn(tmpdir, name='schema.db'):
    """Create a connection with FEAT-048 schema applied."""
    import db as db_module
    conn = sqlite3.connect(os.path.join(tmpdir, name))
    db_module.init_db_schema(conn)
    return conn


def get_table_names(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return [r[0] for r in rows]


def get_column_names(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]


def get_index_names(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    return [r[0] for r in rows]


class TestDbSchemaNewTables(unittest.TestCase):
    """FR-06: New tables added by init_db_schema()."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.conn = make_schema_conn(self.tmpdir)

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_transcript_cursors_table_exists(self):
        """transcript_cursors table must exist after migration."""
        self.assertIn('transcript_cursors', get_table_names(self.conn))

    def test_runtime_events_table_exists(self):
        """runtime_events table must exist after migration."""
        self.assertIn('runtime_events', get_table_names(self.conn))

    def test_connector_diagnostics_table_exists(self):
        """connector_diagnostics table must exist after migration."""
        self.assertIn('connector_diagnostics', get_table_names(self.conn))

    def test_request_fingerprints_table_exists(self):
        """request_fingerprints table must exist after migration (FEAT-049)."""
        self.assertIn('request_fingerprints', get_table_names(self.conn))

    def test_pricing_versions_table_exists(self):
        """pricing_versions table must exist after migration (FEAT-049)."""
        self.assertIn('pricing_versions', get_table_names(self.conn))

    def test_reconciliation_reports_table_exists(self):
        """reconciliation_reports table must exist after migration (FEAT-049)."""
        self.assertIn('reconciliation_reports', get_table_names(self.conn))

    def test_transcript_cursors_columns(self):
        """transcript_cursors must have file_path, byte_pos, file_hash, updated_at."""
        cols = get_column_names(self.conn, 'transcript_cursors')
        for col in ['file_path', 'byte_pos', 'file_hash', 'updated_at']:
            self.assertIn(col, cols, f'Missing column in transcript_cursors: {col}')

    def test_runtime_events_columns(self):
        """runtime_events must have all required columns."""
        cols = get_column_names(self.conn, 'runtime_events')
        for col in ['id', 'event_id', 'timestamp', 'conversation_id',
                    'provider', 'event_type', 'event_data_json']:
            self.assertIn(col, cols, f'Missing column in runtime_events: {col}')

    def test_connector_diagnostics_columns(self):
        """connector_diagnostics must have all required columns."""
        cols = get_column_names(self.conn, 'connector_diagnostics')
        for col in ['id', 'timestamp', 'provider', 'status',
                    'detected_path', 'error_message', 'accuracy_confidence']:
            self.assertIn(col, cols, f'Missing column in connector_diagnostics: {col}')

    def test_request_fingerprints_columns(self):
        """request_fingerprints must have all required columns."""
        cols = get_column_names(self.conn, 'request_fingerprints')
        for col in ['fingerprint', 'provider', 'conv_id', 'request_id',
                    'model', 'timestamp', 'duplicate_count', 'first_seen', 'last_seen']:
            self.assertIn(col, cols, f'Missing column in request_fingerprints: {col}')

    def test_pricing_versions_columns(self):
        """pricing_versions must have all required columns."""
        cols = get_column_names(self.conn, 'pricing_versions')
        for col in ['id', 'provider', 'model', 'version', 'effective_date',
                    'input_per_mtok', 'output_per_mtok', 'cache_read_per_mtok',
                    'cache_write_per_mtok', 'thinking_per_mtok', 'tool_per_mtok', 'created_at']:
            self.assertIn(col, cols, f'Missing column in pricing_versions: {col}')

    def test_reconciliation_reports_columns(self):
        """reconciliation_reports must have all required columns."""
        cols = get_column_names(self.conn, 'reconciliation_reports')
        for col in ['id', 'timestamp', 'requests_discovered', 'requests_parsed',
                    'duplicates_ignored', 'corrupted_transcripts', 'missing_usage_metadata',
                    'reconstructed_usage', 'estimated_usage', 'confidence_score', 'duration_ms']:
            self.assertIn(col, cols, f'Missing column in reconciliation_reports: {col}')


class TestDbSchemaModifiedColumns(unittest.TestCase):
    """provider_requests table extended with accuracy_source, raw_payload, fingerprint, pricing_version, tool_tokens, transcript_offset."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.conn = make_schema_conn(self.tmpdir, 'modified.db')

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_accuracy_source_column_in_provider_requests(self):
        """accuracy_source column must exist in provider_requests."""
        cols = get_column_names(self.conn, 'provider_requests')
        self.assertIn('accuracy_source', cols)

    def test_raw_payload_column_in_provider_requests(self):
        """raw_payload column must exist in provider_requests."""
        cols = get_column_names(self.conn, 'provider_requests')
        self.assertIn('raw_payload', cols)

    def test_fingerprint_column_in_provider_requests(self):
        """fingerprint column must exist in provider_requests (FEAT-049)."""
        cols = get_column_names(self.conn, 'provider_requests')
        self.assertIn('fingerprint', cols)

    def test_pricing_version_column_in_provider_requests(self):
        """pricing_version column must exist in provider_requests (FEAT-049)."""
        cols = get_column_names(self.conn, 'provider_requests')
        self.assertIn('pricing_version', cols)

    def test_tool_tokens_column_in_provider_requests(self):
        """tool_tokens column must exist in provider_requests (FEAT-049)."""
        cols = get_column_names(self.conn, 'provider_requests')
        self.assertIn('tool_tokens', cols)

    def test_transcript_offset_column_in_provider_requests(self):
        """transcript_offset column must exist in provider_requests (FEAT-049)."""
        cols = get_column_names(self.conn, 'provider_requests')
        self.assertIn('transcript_offset', cols)

    def test_runtime_events_no_cost_usd_column(self):
        """FR-07: runtime_events table must NOT have cost_usd (separation)."""
        cols = get_column_names(self.conn, 'runtime_events')
        self.assertNotIn('cost_usd', cols)


class TestDbSchemaIndexes(unittest.TestCase):
    """Required indexes present."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.conn = make_schema_conn(self.tmpdir, 'indexes.db')

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_runtime_events_conv_index_exists(self):
        """idx_runtime_events_conv index must be created."""
        self.assertIn('idx_runtime_events_conv', get_index_names(self.conn))

    def test_runtime_events_type_index_exists(self):
        """idx_runtime_events_type index must be created."""
        self.assertIn('idx_runtime_events_type', get_index_names(self.conn))

    def test_connector_diag_provider_index_exists(self):
        """idx_connector_diag_provider index must be created."""
        self.assertIn('idx_connector_diag_provider', get_index_names(self.conn))

    def test_fingerprints_hash_index_exists(self):
        """idx_fingerprints_hash index must be created (FEAT-049)."""
        self.assertIn('idx_fingerprints_hash', get_index_names(self.conn))

    def test_pricing_versions_effective_index_exists(self):
        """idx_pricing_versions_effective index must be created (FEAT-049)."""
        self.assertIn('idx_pricing_versions_effective', get_index_names(self.conn))

    def test_reconciliation_timestamp_index_exists(self):
        """idx_reconciliation_timestamp index must be created (FEAT-049)."""
        self.assertIn('idx_reconciliation_timestamp', get_index_names(self.conn))


class TestDbSchemaMigrationIdempotent(unittest.TestCase):
    """Schema migration must be safe to run multiple times (NFR-06)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_db_schema_idempotent(self):
        """init_db_schema() can be called twice on the same connection without raising."""
        import db as db_module
        conn = sqlite3.connect(os.path.join(self.tmpdir, 'idempotent.db'))
        try:
            db_module.init_db_schema(conn)
            db_module.init_db_schema(conn)  # second call — must not raise
        except Exception as e:
            self.fail(f'Second init_db_schema() raised: {e}')
        finally:
            conn.close()

    def test_tables_survive_reconnect(self):
        """Tables persist after closing and reopening the connection."""
        import db as db_module
        db_path = os.path.join(self.tmpdir, 'persist.db')
        conn1 = sqlite3.connect(db_path)
        db_module.init_db_schema(conn1)
        conn1.close()

        # Reopen and check
        conn2 = sqlite3.connect(db_path)
        tables = get_table_names(conn2)
        conn2.close()
        self.assertIn('runtime_events', tables)
        self.assertIn('transcript_cursors', tables)


if __name__ == '__main__':
    unittest.main(verbosity=2)
