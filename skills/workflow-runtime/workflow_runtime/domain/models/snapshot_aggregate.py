from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SessionSnapshotEntity:
    snapshot_id: str
    session_id: str
    timestamp: float
    ast_schema_json: str
    state_payload: Dict[str, Any]
    trigger_reason: str

@dataclass
class SnapshotAggregate:
    session_id: str
    max_snapshots: int = 50
    _snapshots: list[SessionSnapshotEntity] = field(default_factory=list[SessionSnapshotEntity])

    def add_snapshot(
        self,
        snapshot_id: str,
        ast_schema_json: str,
        state_payload: Dict[str, Any],
        reason: str = "hmr_update"
    ) -> SessionSnapshotEntity:
        """Creates and appends a snapshot, trimming history to max_snapshots."""
        snapshot = SessionSnapshotEntity(
            snapshot_id=snapshot_id,
            session_id=self.session_id,
            timestamp=time.time(),
            ast_schema_json=ast_schema_json,
            state_payload=state_payload,
            trigger_reason=reason
        )
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots = self._snapshots[-self.max_snapshots:]
        return snapshot

    def get_latest(self) -> Optional[SessionSnapshotEntity]:
        """Returns the most recent snapshot or None if empty."""
        return self._snapshots[-1] if self._snapshots else None

    def get_by_id(self, snapshot_id: str) -> Optional[SessionSnapshotEntity]:
        """Finds a snapshot by unique ID."""
        for snap in self._snapshots:
            if snap.snapshot_id == snapshot_id:
                return snap
        return None

    def get_all_snapshots(self) -> List[SessionSnapshotEntity]:
        """Returns list of snapshots."""
        return list(self._snapshots)
