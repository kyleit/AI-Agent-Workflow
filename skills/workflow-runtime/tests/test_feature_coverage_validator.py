from workflow_runtime.application.workflow.feature_coverage_validator import (
    FeatureCoverageValidator,
)


def test_missing_capability_mapping_blocks_approval() -> None:
    result = FeatureCoverageValidator().validate([{"capability_id": "CAP-1"}])

    assert result.passed is False
    assert "coverage_row_1_missing:phase_id" in result.blocking_findings


def test_complete_unique_capability_rows_pass() -> None:
    row = {
        "capability_id": "CAP-1",
        "user_intent": "validate",
        "acceptance_criteria": ["pass"],
        "phase_id": "P01",
        "code_block_ids": ["B01"],
        "test_ids": ["T01"],
        "evidence_paths": ["docs/evidence.json"],
    }
    assert FeatureCoverageValidator().validate([row]).passed is True
