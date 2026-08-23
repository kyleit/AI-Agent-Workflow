# test_transcript_first_pipeline.py
import unittest
import sqlite3
import tempfile
import os
import sys
import json
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from reconciliation_engine import ReconciliationEngine
from db import init_db_schema
from cost_engine import CostEngine

class TestTranscriptFirstPipeline(unittest.TestCase):
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

    def test_end_to_end_pipeline(self):
        # 1. Write mock transcript file with some turns
        temp_log = tempfile.mktemp(suffix=".jsonl")
        
        # Turn 1: Antigravity turn with usage
        turn1 = {
            "conversation_id": "pipeline-conv",
            "source": "MODEL",
            "type": "PLANNER_RESPONSE",
            "content": "Running task...",
            "usage": {
                "input_tokens": 1000,
                "output_tokens": 500
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        # Turn 2: Duplicate turn (same payload hash and details)
        turn2 = dict(turn1)
        
        with open(temp_log, "w", encoding="utf-8") as f:
            f.write(json.dumps(turn1) + "\n")
            f.write(json.dumps(turn2) + "\n")

        try:
            # 2. Run reconciliation sync
            engine = ReconciliationEngine(self.conn)
            report = engine.sync(transcript_paths=[temp_log])
            
            # 3. Check reports
            self.assertEqual(report.requests_discovered, 2)
            self.assertEqual(report.requests_parsed, 1) # one parsed, one ignored
            self.assertEqual(report.duplicates_ignored, 1)
            self.assertEqual(report.confidence_score, 1.0)
            
            # Check database persistence
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM provider_requests WHERE conversation_id = 'pipeline-conv'")
            self.assertEqual(cursor.fetchone()[0], 1)
            
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
