from workflow_runtime.application.verification.frontend_e2e_gate import (
    validate_real_ui_report_text,
)


def test_real_ui_e2e_rejects_dry_run_mock_memory_and_inference() -> None:
    result = validate_real_ui_report_text(
        "dry-run mockup result inferred from memory", requires_real_ui=True
    )

    assert result.ok is False
    assert result.reason == "frontend_fake_real_ui_evidence"
    assert "dry-run" in result.details["markers"]


def test_real_ui_e2e_accepts_concrete_browser_evidence() -> None:
    result = validate_real_ui_report_text(
        "Playwright CDP browser screenshot and SHA-256 trace", requires_real_ui=True
    )

    assert result.ok is True
