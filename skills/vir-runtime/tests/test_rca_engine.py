# File path: tests/unit/test_rca_engine.py
import unittest
from vir_runtime.domain.evidence import Evidence
from vir_runtime.cognitive.rca import RCAEngine

class TestRCAEngine(unittest.TestCase):
    def setUp(self):
        self.rca_engine = RCAEngine(required_evidence_count=2)
        self.evidence1 = Evidence(source_agent="a", classification="c", payload={})
        self.evidence2 = Evidence(source_agent="b", classification="d", payload={})

    def test_unconfirmed_rca(self):
        # Single evidence should not confirm the root cause
        rc = self.rca_engine.analyze_root_cause("TIMING", "Race condition in click handlers.", [self.evidence1])
        self.assertFalse(rc.is_confirmed)
        self.assertEqual(len(rc.evidence_ids), 1)

    def test_confirmed_rca(self):
        # Two evidence should confirm the root cause
        rc = self.rca_engine.analyze_root_cause("TIMING", "Race condition in click handlers.", [self.evidence1, self.evidence2])
        self.assertTrue(rc.is_confirmed)
        self.assertEqual(len(rc.evidence_ids), 2)

if __name__ == "__main__":
    unittest.main()
