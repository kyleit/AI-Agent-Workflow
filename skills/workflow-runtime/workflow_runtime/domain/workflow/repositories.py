from typing import Protocol

from workflow_runtime.domain.workflow.entities import Checkpoint, WorkflowState


class IWorkflowRepository(Protocol):
    def get_state(self, session_id: str) -> WorkflowState:
        ...

    def save_state(self, state: WorkflowState) -> None:
        ...

    def record_checkpoint(self, checkpoint: Checkpoint) -> None:
        ...

    def list_checkpoints(self, session_id: str) -> list[Checkpoint]:
        ...
