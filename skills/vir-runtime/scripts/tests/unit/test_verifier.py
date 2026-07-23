import pytest
from vir_runtime.varbc.domain.observation import VisualObservation
from vir_runtime.varbc.domain.diff import VisualDiff
from vir_runtime.varbc.domain.report import VARStatus
from vir_runtime.varbc.application.verifier import VARVerifier


def test_verifier_weighted_score_formula():
    verifier = VARVerifier(weight_diff=0.5, weight_layout=0.3, weight_text=0.2, passing_score=85.0)

    # score_diff=100.0, score_layout=90.0, score_text=100.0 -> (0.5*100) + (0.3*90) + (0.2*100) = 50 + 27 + 20 = 97.0
    score = verifier.compute_weighted_score(100.0, 90.0, 100.0)
    assert score == 97.0


@pytest.mark.asyncio
async def test_verifier_verify_pass_and_fail():
    verifier = VARVerifier(passing_score=85.0)

    # Pass scenario
    obs_clean = VisualObservation(id="obs-1", url="http://example.com", console_errors=[])
    diff_clean = VisualDiff(baseline_id="b1", observation_id="obs-1", diff_score=0.02)  # score_diff = 98.0

    report_pass = await verifier.verify([obs_clean], [diff_clean])
    assert report_pass.status == VARStatus.PASS
    assert report_pass.passed is True
    assert report_pass.score >= 85.0

    # Fail scenario: large diff score & console errors
    obs_err = VisualObservation(id="obs-2", url="http://example.com", console_errors=["Error 1"])
    diff_bad = VisualDiff(baseline_id="b2", observation_id="obs-2", diff_score=0.50)  # score_diff = 50.0

    report_fail = await verifier.verify([obs_err], [diff_bad])
    assert report_fail.status == VARStatus.FAIL
    assert report_fail.passed is False
    assert report_fail.score < 85.0
