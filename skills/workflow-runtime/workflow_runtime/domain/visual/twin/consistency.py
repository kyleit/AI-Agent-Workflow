# File path: vir_runtime/twin/consistency.py
from __future__ import annotations

import time
import uuid
from typing import Any


class Contradiction:
    def __init__(self, dimension_a: str, dimension_b: str, description: str, severity: str = "possible") -> None:
        self.id = str(uuid.uuid4())
        self.dimension_a = dimension_a
        self.dimension_b = dimension_b
        self.description = description
        self.severity = severity
        self.timestamp = time.time()


class ConsistencyValidator:
    def validate_consistency(self, dimensions: dict[str, dict[str, Any]]) -> list[Contradiction]:
        """Audit dimensions mapping details for anomalies."""
        contradictions: list[Contradiction] = []

        ui_state = dimensions.get("ui", {})
        network_state = dimensions.get("network", {})

        if ui_state.get("status") == "success" and network_state.get("status_code") == 401:
            contradictions.append(
                Contradiction(
                    dimension_a="ui",
                    dimension_b="network",
                    description="UI indicates success but Network response returned 401 Unauthorized status.",
                    severity="confirmed"
                )
            )

        return contradictions


__all__ = [
    "Contradiction",
    "ConsistencyValidator",
]
