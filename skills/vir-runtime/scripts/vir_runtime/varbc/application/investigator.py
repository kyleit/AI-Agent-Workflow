import uuid
from typing import List, Optional
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.anomaly import Anomaly, AnomalyRule, AnomalySeverity
from vir_runtime.varbc.domain.investigation import Investigation, Hypothesis, HypothesisStatus


class VARInvestigator:
    """Root Cause Analysis (RCA) engine detecting visual anomalies and evaluating hypotheses."""

    def __init__(self, rules: Optional[List[AnomalyRule]] = None) -> None:
        """Constructs RCA engine with optional custom anomaly detection rules."""
        self._rules = rules or self._default_rules()

    def _default_rules(self) -> List[AnomalyRule]:
        """Provides default visual anomaly rules (text overlap, container overflow, misalignment)."""
        return [
            AnomalyRule(
                rule_id="R-01",
                name="Text Overlap",
                pattern="overlap",
                threshold=0.15,
                severity=AnomalySeverity.HIGH,
            ),
            AnomalyRule(
                rule_id="R-02",
                name="Container Overflow",
                pattern="overflow",
                threshold=0.20,
                severity=AnomalySeverity.HIGH,
            ),
            AnomalyRule(
                rule_id="R-03",
                name="Layout Misalignment",
                pattern="misaligned",
                threshold=0.10,
                severity=AnomalySeverity.MEDIUM,
            ),
        ]

    async def investigate(self, observations: List[VisualObservation]) -> Investigation:
        """Analyzes visual observations against anomaly rules to produce an RCA Investigation.

        1. Create unique investigation ID.
        2. Iterate over observations and inspect console_errors and dom_snapshot.
        3. For each triggered rule, construct Hypothesis and evaluate status.
        4. If console_errors exist, mark hypothesis CONFIRMED with error stack evidence.
        5. Compute confidence score based on confirmed hypotheses count.
        6. Return complete Investigation object.
        """
        inv_id = f"inv-{uuid.uuid4().hex[:8]}"
        hypotheses: List[Hypothesis] = []

        for obs in observations:
            # Check console errors
            if obs.console_errors:
                for err in obs.console_errors:
                    hypotheses.append(
                        Hypothesis(
                            statement=f"Browser console error detected: {err}",
                            status=HypothesisStatus.CONFIRMED,
                            evidence=obs.console_errors,
                        )
                    )

            # Inspect DOM snapshot against rules
            dom_lower = obs.dom_snapshot.lower()
            for rule in self._rules:
                if rule.pattern.lower() in dom_lower:
                    hypotheses.append(
                        Hypothesis(
                            statement=f"Visual anomaly rule '{rule.name}' triggered by pattern '{rule.pattern}'",
                            status=HypothesisStatus.CONFIRMED,
                            evidence=[rule.pattern],
                        )
                    )

        confirmed_count = sum(
            1 for h in hypotheses if h.status == HypothesisStatus.CONFIRMED
        )
        confidence = min(1.0, confirmed_count * 0.4) if confirmed_count > 0 else 0.0

        conclusion = (
            f"Investigation completed with {confirmed_count} confirmed findings."
            if confirmed_count > 0
            else "No visual anomalies or console errors detected."
        )

        return Investigation(
            id=inv_id,
            hypotheses=hypotheses,
            conclusion=conclusion,
            confidence=confidence,
            completed=True,
        )
