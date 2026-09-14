from pathlib import Path

from workflow_runtime.application.workflow.source_context_validator import (
    SourceContextValidator,
)


def test_modify_block_requires_real_target_and_symbol(tmp_path: Path) -> None:
    target = tmp_path / "src.py"
    target.write_text("def existing():\n    return 1\n", encoding="utf-8")
    result = SourceContextValidator(tmp_path).validate_blocks([{
        "id": "B01",
        "operation": "modify",
        "file": "src.py",
        "symbol": "missing",
        "implementation_ready": True,
    }])

    assert result.passed is False
    assert "B01:modify_anchor_not_found:missing" in result.blocking_findings


def test_path_escape_is_blocked(tmp_path: Path) -> None:
    result = SourceContextValidator(tmp_path).validate_blocks([{
        "id": "B02",
        "operation": "modify",
        "file": "../outside.py",
        "symbol": "existing",
        "implementation_ready": True,
    }])

    assert result.passed is False
    assert "B02:path_escapes_workspace" in result.blocking_findings


def test_new_file_may_introduce_missing_parent_during_project_init(tmp_path: Path) -> None:
    result = SourceContextValidator(tmp_path).validate_blocks([{
        "id": "B03",
        "operation": "create",
        "file": "internal/domain/monitoring/types.go",
        "implementation_ready": True,
    }])

    assert result.passed is True
    assert "B03:create_parent_missing" not in result.blocking_findings


def test_generated_manifest_may_be_materialized_during_project_init(tmp_path: Path) -> None:
    result = SourceContextValidator(tmp_path).validate_blocks([{
        "id": "B04",
        "operation": "generate",
        "file": "go.sum",
        "implementation_ready": True,
    }])

    assert result.passed is True
    assert "B04:operation_unknown" not in result.blocking_findings
