from __future__ import annotations

import io
import os
from unittest.mock import patch

from workflow_runtime.application.workflow.gate_service import ApprovalGateService, PromptChoice
from workflow_runtime.shared.utils import prompt_select


def test_prompt_select_emits_ask_question_bridge_before_prompt_select_fallback() -> None:
    stdout = io.StringIO()

    with patch("sys.stdout", stdout), patch("sys.stdin", io.StringIO("")):
        with patch.dict(os.environ, {"TEST_PROMPT": "1"}, clear=False):
            result = prompt_select(
                "Approve this release step?",
                ["Continue", "Cancel"],
                default="Cancel",
            )

    output = stdout.getvalue()
    assert result == "PROMPT_UNAVAILABLE"
    assert '<interactive_prompt type="ask_question">' in output
    assert '<interactive_prompt type="select">' in output
    assert output.index('type="ask_question"') < output.index('type="select"')


def test_prompt_select_still_defaults_for_non_approval_empty_stdin() -> None:
    with patch("sys.stdin", io.StringIO("")):
        with patch.dict(os.environ, {"TEST_PROMPT": "1"}, clear=False):
            result = prompt_select("Choose a branch mode?", ["Continue", "Cancel"], default="Cancel")

    assert result == "Cancel"


def test_approval_gate_service_formats_ask_question_before_select_fallback() -> None:
    xml = ApprovalGateService().format_interactive_xml(
        PromptChoice(
            choice_id="release-approval",
            question="Approve this release step?",
            options=["Continue", "Cancel"],
            default_option="Cancel",
        )
    )

    assert '<interactive_prompt type="ask_question">' in xml
    assert '<interactive_prompt type="select">' in xml
    assert xml.index('type="ask_question"') < xml.index('type="select"')
    assert '"preferred_tool": "ask_question"' in xml
    assert '"fallback_tool": "prompt_select"' in xml
