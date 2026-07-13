# test_versioned_pricing.py
import unittest
import sqlite3
import tempfile
import os
import sys
from datetime import datetime, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from cost_engine import CostEngine, ModelPricing
from connectors.base import NormalizedUsageRecord
from db import init_db_schema

class TestVersionedPricing(unittest.TestCase):
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

    def test_effective_date_lookup(self):
        # 1. Insert pricing snapshots
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO pricing_versions (
                provider, model, version, effective_date,
                input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok,
                thinking_per_mtok, tool_per_mtok, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "antigravity", "gemini-test", "1.0.0", "2026-01-01",
            10.0, 20.0, 0.0, 0.0, 0.0, 0.0, datetime.now().isoformat()
        ))
        cursor.execute("""
            INSERT INTO pricing_versions (
                provider, model, version, effective_date,
                input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok,
                thinking_per_mtok, tool_per_mtok, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "antigravity", "gemini-test", "2.0.0", "2026-06-01",
            15.0, 30.0, 0.0, 0.0, 0.0, 0.0, datetime.now().isoformat()
        ))
        self.conn.commit()

        # 2. Test timestamp lookup
        engine = CostEngine(db_conn=self.conn)
        
        # Before version 2.0.0 effective date
        rec1 = NormalizedUsageRecord(
            provider="antigravity",
            model="gemini-test",
            conversation_id="test",
            request_id="1",
            timestamp="2026-03-01T00:00:00Z",
            input_tokens=1000000,
            output_tokens=1000000,
            cache_read_tokens=0,
            cache_write_tokens=0,
            thinking_tokens=0,
            total_tokens=2000000,
            duration_ms=0.0,
            estimated_cost_usd=0.0,
            accuracy_source="estimated"
        )
        res1 = engine.calculate(rec1)
        self.assertEqual(res1.pricing_version, "1.0.0")
        self.assertEqual(res1.cost_usd, 30.0) # 10 + 20

        # After version 2.0.0 effective date
        rec2 = NormalizedUsageRecord(
            provider="antigravity",
            model="gemini-test",
            conversation_id="test",
            request_id="2",
            timestamp="2026-07-01T00:00:00Z",
            input_tokens=1000000,
            output_tokens=1000000,
            cache_read_tokens=0,
            cache_write_tokens=0,
            thinking_tokens=0,
            total_tokens=2000000,
            duration_ms=0.0,
            estimated_cost_usd=0.0,
            accuracy_source="estimated"
        )
        res2 = engine.calculate(rec2)
        self.assertEqual(res2.pricing_version, "2.0.0")
        self.assertEqual(res2.cost_usd, 45.0) # 15 + 30
