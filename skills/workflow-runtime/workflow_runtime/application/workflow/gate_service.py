"""Approval Gate Service handling prompt choices and XML bridge."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from workflow_runtime.shared.utils import atomic_write_json


@dataclass
class PromptChoice:
    choice_id: str
    question: str
    options: list[str]
    default_option: str
    allow_cancel: bool = True


class ApprovalGateService:
    """Service managing pending choices and XML interactive prompts."""

    def __init__(self, runtime_dir: str = ".agents/runtime") -> None:
        self._runtime_dir = Path(runtime_dir)
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        self._recorded_results: dict[str, str] = {}

    def create_prompt_choice(self, choice: PromptChoice) -> dict[str, Any]:
        """Creates a pending prompt choice structure in pending-choice.json."""
        choice_file = self._runtime_dir / "pending-choice.json"
        payload = asdict(choice)
        rel_path = os_relpath_str(choice_file)
        atomic_write_json(rel_path, payload)
        return payload

    def read_prompt_choice(self, choice_id: str) -> dict[str, Any] | None:
        """Reads response choice from choice-response.json if matched."""
        response_file = self._runtime_dir / "choice-response.json"
        if not response_file.exists():
            return None
        with response_file.open(encoding="utf-8") as f:
            data = json.load(f)
        if data.get("choice_id") == choice_id:
            return data
        return None

    def clear_prompt_choice(self, choice_id: str) -> bool:
        """Clears pending choice and response files for choice_id."""
        pending_file = self._runtime_dir / "pending-choice.json"
        response_file = self._runtime_dir / "choice-response.json"
        cleared = False
        if pending_file.exists():
            pending_file.unlink()
            cleared = True
        if response_file.exists():
            response_file.unlink()
            cleared = True
        return cleared

    def format_interactive_xml(self, choice: PromptChoice) -> str:
        """Formats ask_question-first XML with a prompt-select fallback bridge."""
        payload = {
            "choice_id": choice.choice_id,
            "question": choice.question,
            "options": choice.options,
            "default": choice.default_option,
            "allow_cancel": choice.allow_cancel,
            "preferred_tool": "ask_question",
            "fallback_tool": "prompt_select",
            "bridge_order": ["ask_question", "prompt_select", "stdin"],
        }
        options_str = "|".join(choice.options)
        return (
            '<interactive_prompt type="ask_question">\n'
            f"{json.dumps(payload, indent=2, ensure_ascii=False)}\n"
            "</interactive_prompt>\n"
            '<interactive_prompt type="select">\n'
            f"  <question>{choice.question}</question>\n"
            f"  <options>{options_str}</options>\n"
            f"  <default>{choice.default_option}</default>\n"
            "</interactive_prompt>"
        )

    def evaluate_all(self, session_id: str = "") -> dict[str, Any]:
        """Evaluates all pending choices and gate states."""
        pending_file = self._runtime_dir / "pending-choice.json"
        has_pending = pending_file.exists()
        return {
            "session_id": session_id,
            "has_pending_choice": has_pending,
            "recorded_results": dict(self._recorded_results),
        }

    def record_result(self, choice_id: str, choice_value: str) -> None:
        """Records a user response choice result."""
        self._recorded_results[choice_id] = choice_value
        response_file = self._runtime_dir / "choice-response.json"
        payload = {"choice_id": choice_id, "selected_option": choice_value}
        atomic_write_json(os_relpath_str(response_file), payload)


def os_relpath_str(path: Path) -> str:
    import os
    try:
        return os.path.relpath(str(path))
    except ValueError:
        return str(path)


GateService = ApprovalGateService
