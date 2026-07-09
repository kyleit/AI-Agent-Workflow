# test_budget_controller.py
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from budget_controller import evaluate_budget, get_optimization_strategies, apply_optimization

class TestBudgetController(unittest.TestCase):
    def test_healthy_budget(self):
        # 200k tokens out of 2M (10% usage)
        res = evaluate_budget("dummy_conv", 200000)
        self.assertEqual(res["status"], "approved")
        self.assertEqual(res["policy_triggered"], "Healthy")
        self.assertEqual(len(res["recommendations"]), 0)

    def test_high_usage_budget(self):
        # 1.5M tokens out of 2M (75% usage)
        res = evaluate_budget("dummy_conv", 1500000)
        self.assertEqual(res["status"], "approved")
        self.assertEqual(res["policy_triggered"], "High Usage")
        self.assertGreater(len(res["recommendations"]), 0)
        # Ensure strategies are ranked
        self.assertTrue(any(r["name"] == "Reload from Project Memory" for r in res["recommendations"]))

    def test_emergency_blocked_budget(self):
        # 1.95M tokens out of 2M (97.5% usage)
        res = evaluate_budget("dummy_conv", 1950000)
        self.assertEqual(res["status"], "blocked")
        self.assertEqual(res["policy_triggered"], "Emergency Protection")

    def test_apply_optimization_strategy(self):
        res = apply_optimization("dummy_conv", "Remove duplicated workspace reads", 1500000)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["tokens_saved"], 45000)

    def test_budget_mode_toggle(self):
        from budget_controller import set_budget_mode, get_budget_mode
        set_budget_mode("manual")
        self.assertEqual(get_budget_mode(), "manual")
        set_budget_mode("auto")
        self.assertEqual(get_budget_mode(), "auto")
        
    def test_evaluate_budget_extended(self):
        res = evaluate_budget("dummy_conv", 200000)
        self.assertIn("budget_mode", res)
        self.assertIn("current_usage_usd", res)
        self.assertIn("simulation", res)
        sim = res["simulation"]
        self.assertEqual(sim["without_opt_tokens"], 200000)
        self.assertGreaterEqual(sim["without_opt_cost"], 0.0)

if __name__ == "__main__":
    unittest.main()
