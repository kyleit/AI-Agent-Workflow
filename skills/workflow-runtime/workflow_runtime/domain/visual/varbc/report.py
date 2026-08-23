from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from workflow_runtime.domain.visual.varbc.diff import VisualDiff
from workflow_runtime.domain.visual.varbc.observation import VisualObservation


class VARStatus(str, Enum):
    """Status classification for VAR verification execution."""

    PASS = "PASS"
    FAIL = "FAIL"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class VARReport(BaseModel):
    """Aggregated report summarizing visual observations and verification results."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique report identifier")
    observations: list[VisualObservation] = Field(
        default_factory=list[VisualObservation], description="Captured visual observations"
    )
    diffs: list[VisualDiff] = Field(
        default_factory=list[VisualDiff], description="Computed visual diff comparisons"
    )
    status: VARStatus = Field(
        default=VARStatus.NOT_AVAILABLE,
        description="Overall verification status",
    )
    passed: bool = Field(default=False, description="True if status is PASS")
    score: float = Field(
        default=0.0, description="Overall visual compliance score (0.0 to 100.0)"
    )
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), description="UTC generation timestamp"
    )

    def compute_status(self, threshold: float = 0.05) -> VARReport:
        """Calculates status based on maximum diff score against threshold."""
        if not self.diffs:
            return self.model_copy(
                update={
                    "status": VARStatus.NOT_AVAILABLE,
                    "passed": False,
                    "score": 0.0,
                }
            )

        max_diff = max(d.diff_score for d in self.diffs)
        score = round((1.0 - max_diff) * 100.0, 2)
        if score < 0.0:
            score = 0.0

        if max_diff <= threshold:
            status = VARStatus.PASS
            passed = True
        else:
            status = VARStatus.FAIL
            passed = False

        return self.model_copy(
            update={
                "status": status,
                "passed": passed,
                "score": score,
            }
        )


__all__ = [
    "VARStatus",
    "VARReport",
]
