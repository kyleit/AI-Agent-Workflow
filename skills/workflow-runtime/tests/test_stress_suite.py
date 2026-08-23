# test_stress_suite.py
import unittest
import sqlite3
import tempfile
import os
import sys
import json
import time
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from reconciliation_engine import ReconciliationEngine
from db import init_db_schema

class TestStressSuite(unittest.TestCase):
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

    def test_stress_scale(self):
        # Generate 50 conversations with 20 turns each (1000 turns total)
        temp_log = tempfile.mktemp(suffix=".jsonl")
        with open(temp_log, "w", encoding="utf-8") as f:
            for c_id in range(50):
                conv_id = f"stress-conv-{c_id}"
                for turn in range(20):
                    turn_data = {
                        "conversation_id": conv_id,
                        "source": "MODEL",
                        "type": "PLANNER_RESPONSE",
                        "content": f"Planner response turn {turn}",
                        "usage": {
                            "input_tokens": 100 + turn,
                            "output_tokens": 50 + turn
                        },
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                    f.write(json.dumps(turn_data) + "\n")

        try:
            engine = ReconciliationEngine(self.conn)
            start_time = time.time()
            report = engine.sync(transcript_paths=[temp_log])
            duration = time.time() - start_time
            
            # Assertions
            self.assertEqual(report.requests_discovered, 1000)
            self.assertEqual(report.requests_parsed, 1000)
            self.assertEqual(report.duplicates_ignored, 0)
            
            # Performance validation: should be fast (e.g. under 2 seconds)
            self.assertLess(duration, 2.0)
            
        finally:
            if os.path.exists(temp_log):
                os.remove(temp_log)
