"""
Phase boundary controller for AIWF implementation flow.
Evaluates ledger state after each phase completes and recommends next action.
Supports phase resume after interruption.
"""
from __future__ import annotations

from typing import Any, cast

from workflow_runtime.infrastructure.persistence.ledger import (
    PHASE_STATUS_COMPLETED, ImplementationLedger)


class PhaseController:
    """
    Evaluates the implementation ledger after phase transitions.
    Purely computational — no side effects beyond ledger updates.
    """

    def __init__(self, workspace_root: str | None = None) -> None:
        self._workspace_root = workspace_root
        self._ledger = ImplementationLedger(workspace_root)

    def on_phase_completed(self, phase_id: str) -> dict[str, Any]:
        self._ledger.mark_phase_completed(phase_id)

        next_phase = self._ledger.get_next_incomplete_phase()
        feature_complete = self._ledger.is_feature_complete()

        if next_phase is not None:
            return {
                "next_action": "continue_implement",
                "next_phase_id": next_phase,
                "message": (
                    f"✅ {phase_id} completed. Continue with {next_phase}.\n"
                    f"Run: /implement --phase \"{next_phase}\""
                ),
                "release_allowed": False,
            }
        elif feature_complete:
            return {
                "next_action": "debug",
                "next_phase_id": None,
                "message": (
                    "✅ All implementation phases complete!\n"
                    "Next: /debug — Run debug and fix any issues before release."
                ),
                "release_allowed": False,
            }
        else:
            return {
                "next_action": "done",
                "next_phase_id": None,
                "message": "Implementation complete.",
                "release_allowed": False,
            }

    def resume_next_phase(self) -> str | None:
        return self._ledger.get_next_incomplete_phase()

    def get_phase_summary(self) -> list[dict[str, Any]]:
        return self._ledger.get_phase_summary()

    def get_implementation_progress(self) -> dict[str, Any]:
        ledger = self._ledger.load()
        raw_phases = ledger.get("phases", [])
        phases = cast(list[dict[str, Any]], raw_phases) if isinstance(raw_phases, list) else []
        raw_tasks = ledger.get("tasks", {})
        tasks = cast(dict[str, dict[str, Any]], raw_tasks) if isinstance(raw_tasks, dict) else {}

        completed_phases = [p for p in phases if p.get("status") == PHASE_STATUS_COMPLETED]
        remaining_phases = [p for p in phases if p.get("status") != PHASE_STATUS_COMPLETED]
        completed_tasks = [t for t, d in tasks.items() if d.get("status") == "completed"]
        failed_tasks = [t for t, d in tasks.items() if d.get("status") == "failed"]
        pending_tasks = [t for t, d in tasks.items() if d.get("status") == "pending"]

        return {
            "feature_id": ledger.get("feature_id", ""),
            "implementation_status": ledger.get("implementation_status", "not_started"),
            "phases_total": len(phases),
            "phases_completed": len(completed_phases),
            "phases_remaining": len(remaining_phases),
            "tasks_total": len(tasks),
            "tasks_completed": len(completed_tasks),
            "tasks_failed": len(failed_tasks),
            "tasks_pending": len(pending_tasks),
        }


__all__ = ["PhaseController"]
