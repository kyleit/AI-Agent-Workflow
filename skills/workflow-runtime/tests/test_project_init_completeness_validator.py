from workflow_runtime.application.workflow.project_init_completeness_validator import (
    ProjectInitCompletenessValidator,
)


def test_project_init_completeness_blocks_missing_stack_coverage() -> None:
    result = ProjectInitCompletenessValidator().validate(["STACK", "UI"], [{"obligation_id": "STACK"}])

    assert result.passed is False
    assert "project_init_obligation_missing:UI" in result.blocking_findings
    assert "project_init_obligation_incomplete:STACK:scaffold_files" in result.blocking_findings
