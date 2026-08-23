"""Phase Transition Service handling phase progression rules."""

from datetime import datetime, timezone

from workflow_runtime.domain.workflow.entities import Checkpoint, WorkflowState
from workflow_runtime.domain.workflow.repositories import IWorkflowRepository
from workflow_runtime.domain.workflow.value_objects import PhaseStatus, RoleId
from workflow_runtime.shared.errors import StateValidationError

PHASE_ORDER: list[str] = [
    "brainstorming",
    "planning",
    "blueprint",
    "implementation",
    "review",
    "verification",
    "release",
]


class PhaseTransitionService:
    """Service evaluating phase transitions and recorded checkpoints."""

    def __init__(self, repository: IWorkflowRepository) -> None:
        self._repository = repository

    def advance(self, session_id: str, target_phase: str) -> WorkflowState:
        """Advances active workflow state to target phase.

        Raises:
            StateValidationError: If transition is forbidden.
        """
        current_state = self._repository.get_state(session_id)
        if not self.can_transition(current_state.active_phase, target_phase):
            raise StateValidationError(
                f"Cannot transition from '{current_state.active_phase}' to '{target_phase}'."
            )

        updated_state = WorkflowState(
            session_id=current_state.session_id,
            active_phase=target_phase,
            checkpoint=current_state.checkpoint + 1,
            status=PhaseStatus.IN_PROGRESS,
            started_at=current_state.started_at,
            updated_at=datetime.now(timezone.utc),
        )
        self._repository.save_state(updated_state)
        return updated_state

    def advance_phase(self, session_id: str, target_phase: str) -> WorkflowState:
        """Alias for advance method."""
        return self.advance(session_id, target_phase)

    def complete_phase(
        self, session_id: str, phase_name: str, verified_by: RoleId | None = None
    ) -> Checkpoint:
        """Marks current phase complete and records a Checkpoint."""
        current_state = self._repository.get_state(session_id)
        checkpoint = Checkpoint(
            sequence=current_state.checkpoint,
            phase=phase_name,
            status=PhaseStatus.COMPLETED,
            validated_by=verified_by,
            recorded_at=datetime.now(timezone.utc),
        )
        self._repository.record_checkpoint(checkpoint)
        return checkpoint

    def validate_gate(self, session_id: str, phase_name: str) -> bool:
        """Validates whether all gates for a phase have been satisfied."""
        if phase_name not in PHASE_ORDER:
            return False
        checkpoints = self._repository.list_checkpoints(session_id)
        for cp in checkpoints:
            if cp.phase == phase_name and cp.status == PhaseStatus.COMPLETED:
                return True
        return False

    def rollback(self, session_id: str) -> WorkflowState:
        """Rolls back the workflow state to the previous sequential phase.

        Raises:
            StateValidationError: If already at initial phase.
        """
        current_state = self._repository.get_state(session_id)
        if current_state.active_phase not in PHASE_ORDER:
            raise StateValidationError(f"Unknown phase '{current_state.active_phase}'.")

        idx = PHASE_ORDER.index(current_state.active_phase)
        if idx == 0:
            raise StateValidationError("Cannot rollback from initial phase 'brainstorming'.")

        prev_phase = PHASE_ORDER[idx - 1]
        rolled_back_state = WorkflowState(
            session_id=current_state.session_id,
            active_phase=prev_phase,
            checkpoint=max(1, current_state.checkpoint - 1),
            status=PhaseStatus.IN_PROGRESS,
            started_at=current_state.started_at,
            updated_at=datetime.now(timezone.utc),
        )
        self._repository.save_state(rolled_back_state)
        return rolled_back_state

    def can_transition(self, current_phase: str, next_phase: str) -> bool:
        """Checks if moving from current_phase to next_phase is valid."""
        if current_phase not in PHASE_ORDER or next_phase not in PHASE_ORDER:
            return False
        curr_idx = PHASE_ORDER.index(current_phase)
        next_idx = PHASE_ORDER.index(next_phase)
        return next_idx == curr_idx + 1

    def get_next_phase(self, current_phase: str) -> str | None:
        """Returns the next sequential phase name, or None if at final phase."""
        if current_phase not in PHASE_ORDER:
            return None
        idx = PHASE_ORDER.index(current_phase)
        if idx + 1 < len(PHASE_ORDER):
            return PHASE_ORDER[idx + 1]
        return None


PhaseService = PhaseTransitionService
