"""Small compatibility facade for legacy coordinator skill consumers."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from workflow_runtime.infrastructure.session.state_store import StateStore


class GateViolationError(RuntimeError):
    pass


class ParallelGateViolationError(GateViolationError):
    pass


def get_state_store() -> Any:
    return StateStore()


class WorkflowCoordinator:
    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = str(Path(workspace_root).resolve())

    def _state(self) -> dict[str, Any]:
        store = get_state_store()
        value = store.get() if hasattr(store, "get") else {}
        return value if isinstance(value, dict) else {}

    def _check_resume_priority(self) -> tuple[bool, str, str]:
        state = self._state()
        skill = str(state.get("suggested_next_skill") or "")
        command = str(state.get("suggested_next_command") or "")
        return bool(skill), skill, command

    def _verify_blueprint_gate(self, work_item_id: str) -> bool:
        blueprint = self._state().get("blueprint", {})
        if not isinstance(blueprint, dict):
            return False
        scoped = str(blueprint.get("work_item_id") or "")
        return bool(blueprint.get("approved")) and (not scoped or scoped == work_item_id)

    def _verify_safety_gates(self, skill: str, phase: str) -> bool:
        if phase == "implementation" or skill == "blueprint-to-implementation":
            state = self._state()
            blueprint = state.get("blueprint", {})
            if not isinstance(blueprint, dict) or not blueprint.get("approved"):
                raise GateViolationError("Blueprint approval is required before implementation.")
        return True

    def _classify_intent(self, text: str) -> dict[str, str]:
        lowered = text.lower()
        if re.search(r"\b(fix|bug| lỗi|error|crash)\b", lowered):
            return {"skill": "quick-fix", "command": "fix", "phase": "debug"}
        return {"skill": "quick-feature", "command": "feature", "phase": "implementation"}

    def run_tick(self, text: str) -> dict[str, str]:
        if "parallel" in text.lower():
            raise ParallelGateViolationError("Parallel execution requires explicit lane scheduling.")
        result = self._classify_intent(text)
        return {
            "suggested_next_skill": result["skill"],
            "suggested_next_command": result["command"],
            **result,
        }


__all__ = ["GateViolationError", "ParallelGateViolationError", "WorkflowCoordinator", "get_state_store"]
