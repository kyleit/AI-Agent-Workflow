# test_reconciliation_engine.py
import unittest
import sqlite3
import tempfile
import os
import sys
import json
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from reconciliation_engine import ReconciliationEngine, ReconciliationReport
from db import init_db_schema
from connectors import build_default_registry

class TestReconciliationEngine(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.conn = sqlite3.connect(self.db_path)
        init_db_schema(self.conn)

    def tearDown(self):
        self.conn.close()
        os.close(self.db_fd)
        try:
            os.remove(self.db_path)
        except Exception:
            pass

    def test_sync_empty_transcripts(self):
        engine = ReconciliationEngine(db_conn=self.conn)
        report = engine.sync(transcript_paths=[])
        self.assertEqual(report.requests_discovered, 0)
        self.assertEqual(report.requests_parsed, 0)
        self.assertEqual(report.confidence_score, 1.0)

    def test_sync_corrupted_json_lines(self):
        temp_log = tempfile.mktemp(suffix=".jsonl")
        with open(temp_log, "w", encoding="utf-8") as f:
            f.write("invalid json line\n")
            f.write('{"conversation_id": "test", "usage": {"input_tokens": 100}}\n') # missing model
        
        try:
            engine = ReconciliationEngine(db_conn=self.conn)
            report = engine.sync(transcript_paths=[temp_log])
            self.assertEqual(report.requests_discovered, 2)
            self.assertEqual(report.corrupted_transcripts, 1) # first is corrupt
            self.assertEqual(report.requests_parsed, 0) # second fails parse (missing provider/type details)
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
