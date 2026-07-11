# File path: tests/unit/test_consistency_validator.py
import unittest
from vir_runtime.twin.consistency import ConsistencyValidator

class TestConsistencyValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ConsistencyValidator()

    def test_consistent_states(self):
        dimensions = {
            "ui": {"status": "success"},
            "network": {"status_code": 200}
        }
        contradictions = self.validator.validate_consistency(dimensions)
        self.assertEqual(len(contradictions), 0)

    def test_contradicting_states(self):
        dimensions = {
            "ui": {"status": "success"},
            "network": {"status_code": 401}
        }
        contradictions = self.validator.validate_consistency(dimensions)
        self.assertEqual(len(contradictions), 1)
        self.assertEqual(contradictions[0].dimension_a, "ui")
        self.assertEqual(contradictions[0].dimension_b, "network")
        self.assertEqual(contradictions[0].severity, "confirmed")

if __name__ == "__main__":
    unittest.main()
