import uuid
from typing import Optional

from workflow_runtime.application.dtos.snapshot_dtos import (
    SaveSnapshotRequestDTO, SessionSnapshotDTO)
from workflow_runtime.domain.interfaces.snapshot_repository import \
    ISnapshotRepository
from workflow_runtime.domain.models.snapshot_aggregate import SnapshotAggregate


class SaveSnapshotUseCase:
    def __init__(self, repo: ISnapshotRepository):
        self._repo = repo

    def execute(self, request: SaveSnapshotRequestDTO) -> SessionSnapshotDTO:
        """Captures state snapshot and saves to domain aggregate."""
        aggregate = self._repo.get_aggregate(request.session_id)
        if not aggregate:
            aggregate = SnapshotAggregate(session_id=request.session_id)

        snapshot_id = f"snap_{uuid.uuid4().hex[:12]}"
        snapshot = aggregate.add_snapshot(
            snapshot_id=snapshot_id,
            ast_schema_json=request.ast_schema_json,
            state_payload=request.state_payload,
            reason=request.trigger_reason
        )
        self._repo.save_aggregate(aggregate)

        return SessionSnapshotDTO(
            snapshot_id=snapshot.snapshot_id,
            session_id=snapshot.session_id,
            timestamp=snapshot.timestamp,
            ast_schema_json=snapshot.ast_schema_json,
            state_payload=snapshot.state_payload,
            trigger_reason=snapshot.trigger_reason
        )

class RestoreSnapshotUseCase:
    def __init__(self, repo: ISnapshotRepository):
        self._repo = repo

    def execute(self, session_id: str, snapshot_id: Optional[str] = None) -> SessionSnapshotDTO:
        """Retrieves target or latest snapshot for restoration."""
        aggregate = self._repo.get_aggregate(session_id)
        if not aggregate:
            raise ValueError(f"Session with ID '{session_id}' not found.")

        if snapshot_id:
            snapshot = aggregate.get_by_id(snapshot_id)
            if not snapshot:
                raise ValueError(f"Snapshot with ID '{snapshot_id}' not found in session '{session_id}'.")
        else:
            snapshot = aggregate.get_latest()
            if not snapshot:
                raise ValueError(f"No snapshots available for session '{session_id}'.")

        return SessionSnapshotDTO(
            snapshot_id=snapshot.snapshot_id,
            session_id=snapshot.session_id,
            timestamp=snapshot.timestamp,
            ast_schema_json=snapshot.ast_schema_json,
            state_payload=snapshot.state_payload,
            trigger_reason=snapshot.trigger_reason
        )
