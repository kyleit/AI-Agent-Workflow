# File path: tests/unit/test_quality_gate.py
import unittest
from vir_runtime.multi_agent.consensus import ConsensusRecord
from vir_runtime.quality.gate import QualityGateEvaluator

class TestQualityGate(unittest.TestCase):
    def setUp(self):
        self.evaluator = QualityGateEvaluator()

    def test_evaluate_gate_pass(self):
        record = ConsensusRecord(
            verdict="PASS",
            confidence_breakdowns={"design": 0.95, "network": 0.90},
            vetoes=[],
            evidence_ids=[]
        )
        self.assertEqual(self.evaluator.evaluate_gate(record), "PASS")

    def test_evaluate_gate_fail_on_veto(self):
        record = ConsensusRecord(
            verdict="FAIL",
            confidence_breakdowns={"design": 0.95},
            vetoes=["Veto active"],
            evidence_ids=[]
        )
        self.assertEqual(self.evaluator.evaluate_gate(record), "FAIL")

    def test_evaluate_gate_fail_low_confidence(self):
        record = ConsensusRecord(
            verdict="PASS",
            confidence_breakdowns={"design": 0.70}, # Threshold is 0.80 for design
            vetoes=[],
            evidence_ids=[]
        )
        self.assertEqual(self.evaluator.evaluate_gate(record), "FAIL")

if __name__ == "__main__":
    unittest.main()
