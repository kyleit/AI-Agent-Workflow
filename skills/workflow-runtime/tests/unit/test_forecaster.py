# test_forecaster.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import sys
import os

# Adjust path to include scripts directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from forecaster import make_forecast

class TestForecaster(unittest.TestCase):
    def test_empty_events(self):
        result = make_forecast([])
        self.assertEqual(result["exhaustion_probability"], "Low")
        self.assertEqual(result["confidence_level"], "Low")
        self.assertEqual(result["remaining_requests"], 99)

    def test_single_event(self):
        events = [
            {
                "event_type": "Provider request",
                "active_context": 50000,
                "context_delta": 50000,
                "cost": 0.01
            }
        ]
        result = make_forecast(events)
        self.assertEqual(result["confidence_level"], "Low")
        self.assertGreater(result["remaining_requests"], 0)

    def test_multiple_events_normal_growth(self):
        events = [
            {
                "event_type": "Provider request",
                "active_context": 100000,
                "context_delta": 100000,
                "cost": 0.015
            },
            {
                "event_type": "Provider request",
                "active_context": 250000,
                "context_delta": 150000,
                "cost": 0.02
            },
            {
                "event_type": "Provider request",
                "active_context": 450000,
                "context_delta": 200000,
                "cost": 0.025
            }
        ]
        # avg growth of last 3: (100k + 150k + 200k) / 3 = 150k
        # latest context: 450k
        # remaining tokens: 2M - 450k = 1.55M
        # remaining requests: 1.55M / 150k = 10 requests
        result = make_forecast(events, limit=2000000)
        self.assertEqual(result["confidence_level"], "High")
        self.assertEqual(result["remaining_requests"], 10)
        self.assertEqual(result["exhaustion_probability"], "Medium") # 10 requests <= 12 requests

    def test_critical_exhaustion(self):
        events = [
            {
                "event_type": "Provider request",
                "active_context": 1850000,
                "context_delta": 300000,
                "cost": 0.05
            }
        ]
        result = make_forecast(events, limit=2000000)
        self.assertEqual(result["exhaustion_probability"], "Critical")
        self.assertLessEqual(result["remaining_requests"], 3)

if __name__ == "__main__":
    unittest.main()
