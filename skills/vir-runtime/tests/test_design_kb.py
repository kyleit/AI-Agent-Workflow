# File path: tests/unit/test_design_kb.py
import unittest
from vir_runtime.design.kb import DesignKnowledgeBase

class TestDesignKB(unittest.TestCase):
    def setUp(self):
        # Instantiate with default fallback settings
        self.kb = DesignKnowledgeBase(rules_path="nonexistent_rules.yaml", tokens_path="nonexistent_tokens.json")

    def test_lookup_rule(self):
        rule = self.kb.lookup_rule("typography", "font-size")
        self.assertEqual(rule.get("severity"), "MUST")
        self.assertIn("12px", rule.get("allowed", []))

    def test_token_compliance(self):
        # Valid primary color token
        self.assertTrue(self.kb.check_token_compliance("color", "#3b82f6"))
        
        # Invalid color token
        self.assertFalse(self.kb.check_token_compliance("color", "#ff00ff"))

if __name__ == "__main__":
    unittest.main()
