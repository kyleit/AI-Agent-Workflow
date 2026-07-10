# test_fingerprint_engine.py
# Unit tests for FingerprintEngine (FEAT-049 Task 1.1 / Task 4.1)
import os
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from fingerprint_engine import FingerprintEngine, FingerprintEngineError
from db import init_db_schema


class TestFingerprintEngine(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_fp.db")
        self.conn = sqlite3.connect(self.db_path)
        init_db_schema(self.conn)
        self.engine = FingerprintEngine(self.conn)

    def tearDown(self):
        self.conn.close()
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_fingerprint_compute_is_deterministic(self):
        """Fingerprint computation must be stable and identical for identical inputs."""
        fields1 = {
            "provider": "antigravity",
            "conversation_id": "conv-123",
            "request_id": "req-456",
            "response_id": "res-789",
            "model": "gemini-2.5-pro",
            "timestamp": "2026-07-10T00:00:00Z",
            "raw_payload": {"prompt": "hello", "temperature": 0.5}
        }
        fields2 = fields1.copy()

        fp1 = self.engine.compute(fields1)
        fp2 = self.engine.compute(fields2)

        self.assertEqual(fp1, fp2)
        self.assertEqual(len(fp1), 64)
        self.assertTrue(fp1.isalnum())

    def test_fingerprint_compute_missing_fields_defaults(self):
        """compute() must not raise on missing optional fields."""
        fields = {
            "provider": "antigravity",
            "conversation_id": "conv-123"
        }
        fp = self.engine.compute(fields)
        self.assertEqual(len(fp), 64)

    def test_duplicate_detection(self):
        """is_duplicate() should correctly detect registered fingerprints."""
        fields = {
            "provider": "antigravity",
            "conversation_id": "conv-123",
            "request_id": "req-456",
            "response_id": "res-789",
            "model": "gemini-2.5-pro",
            "timestamp": "2026-07-10T00:00:00Z",
            "raw_payload": {"prompt": "hello"}
        }
        fp = self.engine.compute(fields)

        # Before register
        self.assertFalse(self.engine.is_duplicate(fp))

        # Register it
        is_new = self.engine.register(fp, fields)
        self.assertTrue(is_new)

        # After register
        self.assertTrue(self.engine.is_duplicate(fp))

    def test_register_duplicate_increments_count(self):
        """Registering an existing fingerprint increments duplicate_count and returns False."""
        fields = {
            "provider": "antigravity",
            "conversation_id": "conv-123",
            "request_id": "req-456",
            "model": "gemini-2.5-pro"
        }
        fp = self.engine.compute(fields)

        # First registration
        self.assertTrue(self.engine.register(fp, fields))

        # Second registration (collision)
        self.assertFalse(self.engine.register(fp, fields))

        # Check duplicate_count in DB
        cursor = self.conn.cursor()
        cursor.execute("SELECT duplicate_count FROM request_fingerprints WHERE fingerprint = ?", (fp,))
        row = cursor.fetchone()
        self.assertEqual(row[0], 1)

        # Third registration
        self.assertFalse(self.engine.register(fp, fields))
        cursor.execute("SELECT duplicate_count FROM request_fingerprints WHERE fingerprint = ?", (fp,))
        row = cursor.fetchone()
        self.assertEqual(row[0], 2)

    def test_fingerprint_stats(self):
        """get_stats() returns correct totals for unique and duplicate counts."""
        fields1 = {"provider": "antigravity", "request_id": "req-1"}
        fields2 = {"provider": "antigravity", "request_id": "req-2"}

        fp1 = self.engine.compute(fields1)
        fp2 = self.engine.compute(fields2)

        self.engine.register(fp1, fields1)
        self.engine.register(fp2, fields2)
        self.engine.register(fp1, fields1) # duplicate

        stats = self.engine.get_stats()
        self.assertEqual(stats["total_registered"], 2)
        self.assertEqual(stats["total_duplicates"], 1)


if __name__ == '__main__':
    unittest.main()
