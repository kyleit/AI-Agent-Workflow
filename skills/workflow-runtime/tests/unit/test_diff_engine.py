# test_diff_engine.py
import pytest
pytestmark = pytest.mark.unit

import os
import sys
import unittest
import json
import sqlite3

# Ensure scripts dir is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from diff_engine import calculate_diff
from db import save_token_diff, get_token_diff, init_db_schema, PROJECT_DB

class TestDiffEngine(unittest.TestCase):
    
    def test_calculate_diff(self):
        breakdown_a = {
            "request_id": "req_1",
            "total_tokens": 1000,
            "breakdown": [
                { "category": "Conversation History", "tokens": 600, "percentage": 60.0 },
                { "category": "AI_RULES", "tokens": 250, "percentage": 25.0 },
                { "category": "AGENTS", "tokens": 150, "percentage": 15.0 }
            ]
        }
        
        breakdown_b = {
            "request_id": "req_2",
            "total_tokens": 1500,
            "breakdown": [
                { "category": "Conversation History", "tokens": 900, "percentage": 60.0 },
                { "category": "AI_RULES", "tokens": 200, "percentage": 13.33 },
                { "category": "AGENTS", "tokens": 300, "percentage": 20.0 },
                { "category": "Blueprints", "tokens": 100, "percentage": 6.67 }
            ]
        }
        
        diff = calculate_diff(breakdown_a, breakdown_b)
        
        self.assertEqual(diff["net_change_tokens"], 500)
        self.assertEqual(diff["percentage_change"], 50.0)
        self.assertEqual(diff["added_tokens"], 550) # Conversation History +300, AGENTS +150, Blueprints +100
        self.assertEqual(diff["removed_tokens"], 50) # AI_RULES -50
        
        categories = diff["categories"]
        self.assertEqual(categories["Conversation History"]["delta"], 300)
        self.assertEqual(categories["AI_RULES"]["delta"], -50)
        self.assertEqual(categories["Blueprints"]["delta"], 100)

    def test_db_persistence(self):
        diff_data = {
            "request_id": "test_req_2",
            "prev_request_id": "test_req_1",
            "conversation_id": "test_conv",
            "net_change_tokens": 300,
            "percentage_change": 30.0,
            "added_tokens": 350,
            "removed_tokens": 50,
            "categories": {
                "Conversation History": {
                    "previous": 600,
                    "current": 900,
                    "delta": 300,
                    "percentage": 50.0
                }
            },
            "timestamp": "2026-07-09T00:00:00Z"
        }
        
        save_token_diff(diff_data)
        retrieved = get_token_diff("test_req_2")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["prev_request_id"], "test_req_1")
        self.assertEqual(retrieved["net_change_tokens"], 300)
        self.assertEqual(retrieved["categories"]["Conversation History"]["delta"], 300)

if __name__ == "__main__":
    unittest.main()
