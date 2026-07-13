# phase_controller.py
"""
Phase boundary controller for AIWF implementation flow.
Evaluates ledger state after each phase completes and recommends next action.
Supports phase resume after interruption.
"""
from datetime import datetime, timezone
from typing import Optional

from ledger import (  # type: ignore
    ImplementationLedger,
    PHASE_STATUS_COMPLETED, PHASE_STATUS_PENDING, PHASE_STATUS_IN_PROGRESS,
)


class PhaseController:
    """
    Evaluates the implementation ledger after phase transitions.
    Purely computational — no side effects beyond ledger updates.
    Works without FEAT-052 Worker Manager (optional dependency).
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root
        self._ledger = ImplementationLedger(workspace_root)

    def on_phase_completed(self, phase_id: str) -> dict:
        """
        Called after a phase finishes implementation.
        Updates ledger, computes next action, returns structured result.
        
        Args:
            phase_id: The ID of the phase that just completed.
        
        Returns:
            {
                next_action: "continue_implement" | "debug" | "done",
                next_phase_id: str | None,
                message: str,
                release_allowed: bool,
            }
        """
        # Mark phase as completed in ledger
        self._ledger.mark_phase_completed(phase_id)

        # Find next incomplete phase
        next_phase = self._ledger.get_next_incomplete_phase()
        feature_complete = self._ledger.is_feature_complete()

        if next_phase is not None:
            # More phases to implement
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
            # All phases done → move to debug
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

    def resume_next_phase(self) -> Optional[str]:
        """
        Find the next incomplete phase and return its ID.
        Returns None if all phases are complete.
        Used by: workflow_runtime.py implement resume
        """
        return self._ledger.get_next_incomplete_phase()

    def get_phase_summary(self) -> list[dict]:
        """Return list of phase statuses for display."""
        return self._ledger.get_phase_summary()

    def get_implementation_progress(self) -> dict:
        """Return structured progress overview."""
        ledger = self._ledger.load()
        phases = ledger.get("phases", [])
        tasks = ledger.get("tasks", {})

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
            "current_phase": ledger.get("current_phase"),
            "next_phase": self.resume_next_phase(),
            "all_complete": self._ledger.is_feature_complete(),
        }
