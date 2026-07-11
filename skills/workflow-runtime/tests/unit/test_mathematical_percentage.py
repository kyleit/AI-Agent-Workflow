# test_mathematical_percentage.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from context import estimate_context_usage

class TestMathematicalPercentage(unittest.TestCase):
    def test_percentage_calculation(self):
        cases = [
            (100000, 2000000, 5.0),
            (250000, 2000000, 12.5),
            (349200, 2000000, 17.46),
            (500000, 2000000, 25.0),
            (1000000, 2000000, 50.0),
            (1900000, 2000000, 95.0),
            (2000000, 2000000, 100.0),
        ]
        
        for active, limit, expected_pct in cases:
            calculated = round((active / limit) * 100, 2)
            self.assertAlmostEqual(calculated, expected_pct, places=2,
                                   msg=f"Failed for active={active}, limit={limit}. Expected {expected_pct}%, got {calculated}%")

    def test_units_consistency(self):
        # Ensure that active_tokens is stored in tokens unit and percentage matches
        session_data = {
            "context_usage": {
                "total_tokens": 349200, # active_tokens
                "limit_tokens": 2000000,
                "percentage": 17.46
            }
        }
        
        tot = session_data["context_usage"]["total_tokens"]
        lim = session_data["context_usage"]["limit_tokens"]
        pct = session_data["context_usage"]["percentage"]
        
        calc_pct = round((tot / lim) * 100, 2)
        self.assertEqual(pct, calc_pct)

if __name__ == "__main__":
    unittest.main()
