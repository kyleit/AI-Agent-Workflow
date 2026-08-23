# test_insights_engine.py
import pytest
pytestmark = pytest.mark.unit

import sys
import os
import unittest
import tempfile
import sqlite3
import json

# Add scripts directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

import insights_engine
import db

class TestInsightsEngine(unittest.TestCase):
    def setUp(self):
        # Redirect DB to a temp location for unit test safety
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp()
        db.PROJECT_DB = self.temp_db_path
        
    def tearDown(self):
        os.close(self.temp_db_fd)
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

    def test_efficiency_score_calculation(self):
        # Empty requests list
        self.assertEqual(insights_engine.calculate_efficiency_score([]), 100)
        
        # Highly efficient requests
        reqs = [
            {"total_tokens": 10000, "cost_usd": 0.005, "tool_call_count": 2},
            {"total_tokens": 20000, "cost_usd": 0.006, "tool_call_count": 3}
        ]
        self.assertEqual(insights_engine.calculate_efficiency_score(reqs), 100)
        
        # Heavy/inefficient requests
        reqs_heavy = [
            {"total_tokens": 1200000, "cost_usd": 0.36, "tool_call_count": 20},
            {"total_tokens": 1400000, "cost_usd": 0.42, "tool_call_count": 22}
        ]
        score = insights_engine.calculate_efficiency_score(reqs_heavy)
        self.assertLess(score, 100)
        self.assertGreaterEqual(score, 10)

    def test_recommendations_generation(self):
        # Conversation history > 50%
        requests = [
            {
                "total_tokens": 100000,
                "context_breakdown_json": json.dumps({
                    "breakdown": [
                        {"category": "Conversation History", "tokens": 70000},
                        {"category": "AI_RULES", "tokens": 10000}
                    ]
                })
            }
        ]
        recs = insights_engine.generate_recommendations(requests, "test_conv_id")
        rec_types = [r["type"] for r in recs]
        self.assertIn("Reduce Conversation History", rec_types)

    def test_db_persistence(self):
        # Test saving and loading snapshots
        snapshot = {
            "timestamp": "2026-07-09T00:00:00Z",
            "conversation_id": "test_conv_id",
            "efficiency_score": 92,
            "avg_tokens": 45000,
            "avg_cost": 0.015,
            "growth_trend": "stable",
            "insight_data": {"test_key": "test_val"}
        }
        db.save_insight_snapshot(snapshot)
        
        snaps = db.get_insight_snapshots("test_conv_id")
        self.assertEqual(len(snaps), 1)
        self.assertEqual(snaps[0]["efficiency_score"], 92)
        self.assertEqual(snaps[0]["insight_data"].get("test_key"), "test_val")

        # Test saving and accepting recommendations
        rec = {
            "id": "rec_123",
            "conversation_id": "test_conv_id",
            "type": "Reduce Conversation History",
            "description": "Clean up history",
            "token_savings": 5000,
            "cost_savings": 0.015,
            "priority": "High",
            "confidence": 0.90,
            "status": "pending",
            "timestamp": "2026-07-09T00:00:00Z"
        }
        db.save_recommendations([rec])
        
        recs = db.get_recommendations("test_conv_id")
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]["status"], "pending")
        
        # Update status
        success = db.update_recommendation_status("rec_123", "accepted")
        self.assertTrue(success)
        
        recs_after = db.get_recommendations("test_conv_id")
        self.assertEqual(recs_after[0]["status"], "accepted")

if __name__ == "__main__":
    unittest.main()
