from workflow_runtime.application.workflow.blueprint_scope_decomposer import (
    BlueprintScopeDecomposer,
)


def test_large_feature_requires_rational_phase_split() -> None:
    result = BlueprintScopeDecomposer().assess(8, 5, 12, True)

    assert result.requires_phase_split is True
    assert result.recommended_phase_count == 3
    assert "cross_layer_scope" in result.reasons


def test_boundary_kinds_control_phase_count() -> None:
    result = BlueprintScopeDecomposer().assess(2, 1, 2, False, ["backend", "frontend", "e2e"])

    assert result.recommended_phase_count == 3
    assert result.boundary_plan == ["backend", "frontend", "e2e"]
