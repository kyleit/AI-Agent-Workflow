from __future__ import annotations

import io
import os
import json
from unittest.mock import patch

from workflow_runtime.application.workflow.gate_service import ApprovalGateService, PromptChoice
from workflow_runtime.shared.utils import prompt_select


def test_prompt_select_emits_ask_question_bridge_before_prompt_select_fallback() -> None:
    stdout = io.StringIO()

    with patch("sys.stdout", stdout), patch("sys.stdin", io.StringIO("")):
        with patch.dict(
            os.environ,
            {"TEST_PROMPT": "1", "AIWF_PROMPT_WAIT_SECONDS": "0"},
            clear=False,
        ):
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


def test_prompt_select_accepts_one_shot_agent_response_without_stdin() -> None:
    stdout = io.StringIO()

    with patch("sys.stdout", stdout), patch("sys.stdin", io.StringIO("")):
        with patch.dict(
            os.environ,
            {"TEST_PROMPT": "1", "AIWF_PROMPT_RESPONSE": "Continue"},
            clear=False,
        ):
            result = prompt_select(
                "Approve this release step?",
                ["Continue", "Cancel"],
                default="Cancel",
            )

    assert result == "Continue"


def test_prompt_select_reads_agent_response_file_by_choice_id(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    response_dir = tmp_path / ".agents" / "runtime"
    response_dir.mkdir(parents=True)
    response_file = response_dir / "prompt-response.json"

    question = "Approve this release step?"
    options = ["Continue", "Cancel"]
    from workflow_runtime.shared.utils import prompt_choice_id

    response_file.write_text(
        json.dumps(
            {
                "choice_id": prompt_choice_id(question, options),
                "selected_option": "Continue",
            }
        ),
        encoding="utf-8",
    )

    with patch("sys.stdout", io.StringIO()), patch("sys.stdin", io.StringIO("")):
        with patch.dict(
            os.environ,
            {"TEST_PROMPT": "1", "AIWF_PROMPT_RESPONSE_FILE": str(response_file.relative_to(tmp_path))},
            clear=False,
        ):
            result = prompt_select(question, options, default="Cancel")

    assert result == "Continue"
    assert not response_file.exists()
