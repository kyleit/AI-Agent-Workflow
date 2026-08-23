# File path: vir_runtime/quality/gate.py
from __future__ import annotations

import os
from typing import Any, cast

import yaml

from workflow_runtime.domain.ports.visual_ports import ConsensusRecord


class QualityGateEvaluator:
    def __init__(self, config_path: str = "config.yaml") -> None:
        self.config_path = config_path
        self.thresholds: dict[str, Any] = {"visual_regression": 0.90, "accessibility": 1.00, "design": 0.80}
        self._load_config()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                raw_config = yaml.safe_load(f)
            config = cast(dict[str, Any], raw_config) if isinstance(raw_config, dict) else {}
            qg_dict = cast(dict[str, Any], config.get("quality_gate")) if isinstance(config.get("quality_gate"), dict) else {}
            thresh = cast(dict[str, Any], qg_dict.get("thresholds")) if isinstance(qg_dict.get("thresholds"), dict) else self.thresholds
            self.thresholds = thresh

    def evaluate_gate(self, record: ConsensusRecord) -> str:
        """Evaluate ConsensusRecords against threshold rules and return gate results."""
        if not record or not hasattr(record, "confidence_breakdowns"):
            return "BLOCKED"

        if len(record.vetoes) >= 1:
            return "FAIL"

        for domain, confidence in record.confidence_breakdowns.items():
            threshold = float(cast(float, self.thresholds.get(domain, 0.85)))
            if confidence < threshold:
                return "FAIL"

        return "PASS"


__all__ = ["QualityGateEvaluator"]
