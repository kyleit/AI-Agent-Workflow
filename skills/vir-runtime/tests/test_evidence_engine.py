# File path: tests/unit/test_evidence_engine.py
import unittest
import tempfile
import os
from dataclasses import FrozenInstanceError
from vir_runtime.domain.evidence import Evidence
from vir_runtime.domain.evidence_engine import EvidenceEngine

class TestEvidenceEngine(unittest.TestCase):
    def setUp(self):
        # Create a temporary DB path
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            self.db_path = tmp.name
        self.engine = EvidenceEngine(db_path=self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_evidence_immutability(self):
        evidence = Evidence(
            source_agent="visual_agent",
            classification="ui_regression",
            payload={"diff": 0.05}
        )
        # Attempting to modify properties should raise FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):
            evidence.source_agent = "new_agent" # type: ignore

    def test_add_and_query_evidence(self):
        evidence1 = Evidence(
            source_agent="visual_agent",
            classification="ui_regression",
            payload={"diff": 0.05}
        )
        evidence2 = Evidence(
            source_agent="network_agent",
            classification="status_code_mismatch",
            payload={"code": 404}
        )

        self.engine.add_evidence(evidence1)
        self.engine.add_evidence(evidence2)

        # Query by source_agent
        results = self.engine.query_evidence({"source_agent": "visual_agent"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].evidence_id, evidence1.evidence_id)
        self.assertEqual(results[0].payload["diff"], 0.05)

        # Query all (empty filter)
        all_results = self.engine.query_evidence({})
        self.assertEqual(len(all_results), 2)

if __name__ == "__main__":
    unittest.main()
