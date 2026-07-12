# test_optimizer.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from optimizer import (
    init_optimizer_tables,
    get_active_policy,
    set_active_policy,
    calculate_roi,
    generate_benchmark_report,
    get_optimization_leaderboard
)

from budget_controller import init_budget_tables

class TestOptimizer(unittest.TestCase):
    def setUp(self):
        init_optimizer_tables()
        init_budget_tables()

    def test_policy_switching(self):
        res = set_active_policy("Aggressive")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["active_policy"], "Aggressive")
        
        policy = get_active_policy()
        self.assertEqual(policy["name"], "Aggressive")
        self.assertEqual(policy["compression_pct"], 90.0)

    def test_calculate_roi(self):
        res = calculate_roi("dummy_conv")
        self.assertEqual(res["conversation_id"], "dummy_conv")
        self.assertGreaterEqual(res["total_tokens_saved"], 0)

    def test_generate_benchmark_report(self):
        # Set balanced policy for 75% savings target
        set_active_policy("Balanced")
        res = generate_benchmark_report(100000, 10.0)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["original_tokens"], 100000)
        self.assertEqual(res["optimized_tokens"], 25000) # 75% savings
        self.assertEqual(res["tokens_saved"], 75000)
        self.assertEqual(res["original_cost"], 10.0)
        self.assertEqual(res["optimized_cost"], 2.50)
        self.assertEqual(res["cost_saved"], 7.50)

    def test_leaderboard(self):
        board = get_optimization_leaderboard()
        self.assertGreater(len(board), 0)
        self.assertEqual(board[0]["skill"], "blueprint-to-implementation")

if __name__ == "__main__":
    unittest.main()
