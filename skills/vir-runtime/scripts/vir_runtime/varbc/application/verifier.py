import uuid
from typing import List
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.diff import VisualDiff
from vir_runtime.varbc.domain.report import VARReport, VARStatus


class VARVerifier:
    """Weighted Consensus Quality Gate calculating visual verification scores."""

    def __init__(
        self,
        weight_diff: float = 0.5,
        weight_layout: float = 0.3,
        weight_text: float = 0.2,
        passing_score: float = 85.0,
    ) -> None:
        """Initializes Quality Gate with configurable consensus weights."""
        assert abs((weight_diff + weight_layout + weight_text) - 1.0) < 1e-5, "Weights must sum to 1.0"
        self._w_diff = weight_diff
        self._w_layout = weight_layout
        self._w_text = weight_text
        self._passing_score = passing_score

    def compute_weighted_score(
        self, score_diff: float, score_layout: float, score_text: float
    ) -> float:
        """Calculates final weighted visual quality score from 0.0 to 100.0.

        FinalScore = (w_diff * score_diff) + (w_layout * score_layout) + (w_text * score_text)
        """
        return (
            (self._w_diff * score_diff)
            + (self._w_layout * score_layout)
            + (self._w_text * score_text)
        )

    async def verify(
        self, observations: List[VisualObservation], diffs: List[VisualDiff]
    ) -> VARReport:
        """Evaluates observations and diffs to produce a final Quality Gate VARReport.

        1. Calculate average diff score across diffs list (0.0 if empty).
        2. Calculate score_diff = (1.0 - avg_diff) * 100.0.
        3. Evaluate score_layout based on DOM structure stability (default 90.0).
        4. Evaluate score_text based on console errors presence (100.0 if empty, 50.0 if errors exist).
        5. Calculate final_score = compute_weighted_score(score_diff, score_layout, score_text).
        6. Determine passed = final_score >= self._passing_score.
        7. Set status = VARStatus.PASS if passed else VARStatus.FAIL.
        8. Return constructed VARReport instance.
        """
        avg_diff = (
            sum(d.diff_score for d in diffs) / len(diffs) if diffs else 0.0
        )
        score_diff = (1.0 - avg_diff) * 100.0

        score_layout = 90.0
        has_console_errors = any(
            bool(obs.console_errors) for obs in observations
        )
        score_text = 50.0 if has_console_errors else 100.0

        final_score = self.compute_weighted_score(score_diff, score_layout, score_text)
        passed = final_score >= self._passing_score
        status = VARStatus.PASS if passed else VARStatus.FAIL

        report_id = f"rep-{uuid.uuid4().hex[:8]}"
        return VARReport(
            id=report_id,
            observations=observations,
            diffs=diffs,
            status=status,
            passed=passed,
            score=round(final_score, 2),
        )
