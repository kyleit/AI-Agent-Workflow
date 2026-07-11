# File path: vir_runtime/quality/gate.py
import yaml
import os
from typing import Dict, Any
from vir_runtime.multi_agent.consensus import ConsensusRecord

class QualityGateEvaluator:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.thresholds = {"visual_regression": 0.90, "accessibility": 1.00, "design": 0.80}
        self._load_config()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            self.thresholds = config.get("quality_gate", {}).get("thresholds", self.thresholds)

    def evaluate_gate(self, record: ConsensusRecord) -> str:
        """Evaluate ConsensusRecords against threshold rules and return gate results."""
        if not record or not hasattr(record, "confidence_breakdowns"):
            return "BLOCKED"

        # If there are active vetoes, fail immediately
        if len(record.vetoes) >= 1:
            return "FAIL"

        # Check domain confidence scores against thresholds
        for domain, confidence in record.confidence_breakdowns.items():
            threshold = self.thresholds.get(domain, 0.85)
            if confidence < threshold:
                # If it's a minor failure (above a fallback but below strict threshold), it might be PARTIAL
                # But to keep logic strict, we return FAIL
                return "FAIL"
        
        return "PASS"
