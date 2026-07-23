import pytest
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.investigation import HypothesisStatus
from vir_runtime.varbc.application.investigator import VARInvestigator


@pytest.mark.asyncio
async def test_investigator_detects_console_errors_and_anomalies():
    investigator = VARInvestigator()

    obs1 = VisualObservation(
        id="obs-1",
        url="http://example.com",
        dom_snapshot="<div class='text overlap'>Overlapping content</div>",
        console_errors=["Uncaught TypeError: Cannot read property of null"],
    )

    investigation = await investigator.investigate([obs1])

    assert investigation.completed is True
    assert len(investigation.hypotheses) == 2

    # Check console error hypothesis
    console_hyp = [h for h in investigation.hypotheses if "console error" in h.statement.lower()][0]
    assert console_hyp.status == HypothesisStatus.CONFIRMED

    # Check pattern hypothesis
    rule_hyp = [h for h in investigation.hypotheses if "overlap" in h.statement.lower()][0]
    assert rule_hyp.status == HypothesisStatus.CONFIRMED

    assert investigation.confidence > 0.0


@pytest.mark.asyncio
async def test_investigator_clean_observation():
    investigator = VARInvestigator()

    obs_clean = VisualObservation(
        id="obs-2",
        url="http://example.com",
        dom_snapshot="<div>Clean layout</div>",
        console_errors=[],
    )

    investigation = await investigator.investigate([obs_clean])

    assert investigation.completed is True
    assert len(investigation.hypotheses) == 0
    assert investigation.confidence == 0.0
    assert "No visual anomalies" in investigation.conclusion
