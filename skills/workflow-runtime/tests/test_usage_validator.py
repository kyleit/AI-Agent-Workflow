# test_usage_validator.py
import unittest
import sqlite3
import tempfile
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from usage_validator import UsageValidator
from db import init_db_schema

class TestUsageValidator(unittest.TestCase):
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

    def test_validate_negative_tokens(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO provider_requests (
                request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
                model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
                thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
                memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "req-1", "wf-1", "conv-1", "proj-1", "skill-1", "cmd-1",
            "model-1", "provider-1", datetime.now(timezone.utc).isoformat(), 1.0, -50, 100, 0,
            0, 50, 0.01, 0, 0, 0, 0, 0.0, 1000000, "success"
        ))
        self.conn.commit()

        validator = UsageValidator(self.conn)
        res = validator.validate()
        self.assertEqual(res["status"], "violations")
        self.assertEqual(res["count"], 1)
        self.assertEqual(res["violations"][0]["type"], "negative_value")
        self.assertEqual(res["violations"][0]["field"], "input_tokens")

    def test_validate_future_timestamp(self):
        future_time = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO provider_requests (
                request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
                model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
                thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
                memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "req-2", "wf-1", "conv-1", "proj-1", "skill-1", "cmd-1",
            "model-1", "provider-1", future_time, 1.0, 100, 100, 0,
            0, 200, 0.01, 0, 0, 0, 0, 0.0, 1000000, "success"
        ))
        self.conn.commit()

        validator = UsageValidator(self.conn)
        res = validator.validate()
        self.assertEqual(res["status"], "violations")
        self.assertEqual(res["violations"][0]["type"], "future_timestamp")
