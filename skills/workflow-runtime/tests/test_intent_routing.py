# test_intent_routing.py
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".agents", "skills", "workflow-coordinator", "scripts")))
from coordinator import WorkflowCoordinator

class TestIntentRouting(unittest.TestCase):
    def test_classify_intent_fix(self):
        coord = WorkflowCoordinator()
        res = coord._classify_intent("fix ticket 12")
        self.assertEqual(res["skill"], "quick-fix")
        self.assertEqual(res["command"], "fix")
        self.assertEqual(res["phase"], "debug")

    def test_classify_intent_feature(self):
        coord = WorkflowCoordinator()
        res = coord._classify_intent("add new visual editor feature")
        self.assertEqual(res["skill"], "quick-feature")
        self.assertEqual(res["command"], "feature")
        self.assertEqual(res["phase"], "implementation")

if __name__ == "__main__":
    unittest.main()
