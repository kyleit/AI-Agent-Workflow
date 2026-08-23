from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from workflow_runtime.domain.workflow.value_objects import PhaseStatus, RoleId


@dataclass
class Checkpoint:
    sequence: int
    phase: str
    status: PhaseStatus
    validated_by: RoleId | None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid(self) -> bool:
        return self.sequence > 0 and bool(self.phase and self.phase.strip())


@dataclass
class Phase:
    name: str
    order: int
    required_roles: list[RoleId] = field(default_factory=list[RoleId])

    def is_gate_phase(self) -> bool:
        return len(self.required_roles) > 0

    def can_transition_from(self, previous_phase: str) -> bool:
        return bool(previous_phase)


@dataclass
class WorkflowState:
    session_id: str
    active_phase: str
    checkpoint: int
    status: PhaseStatus
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_blocked(self) -> bool:
        return self.status == PhaseStatus.BLOCKED

    def advance_to(self, phase: str) -> "WorkflowState":
        self.active_phase = phase
        self.checkpoint += 1
        self.status = PhaseStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)
        return self

    def mark_failed(self, reason: str = "") -> "WorkflowState":
        self.status = PhaseStatus.FAILED
        self.updated_at = datetime.now(timezone.utc)
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active_phase": self.active_phase,
            "checkpoint": self.checkpoint,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
