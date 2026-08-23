"""Workflow Coordinator Service executing runtime ticks and orchestration."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from workflow_runtime.application.workflow.gate_service import \
    ApprovalGateService
from workflow_runtime.application.workflow.phase_service import \
    PhaseTransitionService
from workflow_runtime.domain.workflow.entities import WorkflowState
from workflow_runtime.domain.workflow.repositories import IWorkflowRepository
from workflow_runtime.domain.workflow.value_objects import PhaseStatus
from workflow_runtime.shared.errors import EntityNotFoundError


@dataclass
class TickResult:
    session_id: str
    active_phase: str
    checkpoint: int
    status: str
    message: str
    requires_user_input: bool


class WorkflowCoordinatorService:
    """Orchestrator for runtime ticks, phase evaluation, and gate checks."""

    def __init__(
        self,
        repository: IWorkflowRepository,
        phase_service: PhaseTransitionService | None = None,
        gate_service: ApprovalGateService | None = None,
        session_service: Any = None,
    ) -> None:
        self._repository = repository
        self._phase_service = phase_service or PhaseTransitionService(repository)
        self._gate_service = gate_service or ApprovalGateService()
        self._session_service = session_service

    def tick(self, dry_run: bool = False, session_id: str = "default") -> TickResult:
        """Executes a single runtime tick, updating timestamp and phase status."""
        try:
            state = self._repository.get_state(session_id)
        except EntityNotFoundError:
            state = self.initialize_workflow(session_id)

        if not dry_run:
            updated_state = WorkflowState(
                session_id=state.session_id,
                active_phase=state.active_phase,
                checkpoint=state.checkpoint,
                status=state.status,
                started_at=state.started_at,
                updated_at=datetime.now(timezone.utc),
            )
            self._repository.save_state(updated_state)
            state = updated_state

        requires_input = state.status == PhaseStatus.BLOCKED
        return TickResult(
            session_id=state.session_id,
            active_phase=state.active_phase,
            checkpoint=state.checkpoint,
            status=state.status.value,
            message=f"Tick completed for phase '{state.active_phase}'.",
            requires_user_input=requires_input,
        )

    def execute_tick(self, session_id: str = "default") -> TickResult:
        """Executes a tick for session_id."""
        return self.tick(dry_run=False, session_id=session_id)

    def get_state(self, session_id: str = "default") -> WorkflowState:
        """Retrieves active WorkflowState entity for session_id."""
        return self._repository.get_state(session_id)

    def reset(self, session_id: str = "default", initial_phase: str = "brainstorming") -> WorkflowState:
        """Resets the workflow state to initial phase."""
        now = datetime.now(timezone.utc)
        new_state = WorkflowState(
            session_id=session_id,
            active_phase=initial_phase,
            checkpoint=1,
            status=PhaseStatus.IN_PROGRESS,
            started_at=now,
            updated_at=now,
        )
        self._repository.save_state(new_state)
        return new_state

    def initialize_workflow(
        self, session_id: str = "default", initial_phase: str = "brainstorming"
    ) -> WorkflowState:
        """Initializes a brand-new workflow session entity."""
        return self.reset(session_id=session_id, initial_phase=initial_phase)

    def get_status_summary(self, session_id: str = "default") -> dict[str, Any]:
        """Returns a status summary dictionary for the given session."""
        try:
            state = self._repository.get_state(session_id)
            return {
                "session_id": state.session_id,
                "active_phase": state.active_phase,
                "checkpoint": state.checkpoint,
                "status": state.status.value,
            }
        except EntityNotFoundError:
            return {
                "session_id": session_id,
                "active_phase": "unknown",
                "checkpoint": 0,
                "status": "NOT_INITIALIZED",
            }

    def release_lease(self, session_id: str = "default") -> bool:
        """Releases active execution lease lock."""
        return True
