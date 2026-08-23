import threading
from typing import Dict, Optional

from workflow_runtime.domain.interfaces.snapshot_repository import \
    ISnapshotRepository
from workflow_runtime.domain.models.snapshot_aggregate import SnapshotAggregate


class InMemorySnapshotRepository(ISnapshotRepository):
    """Thread-safe InMemorySnapshotRepository storing up to 50 historical state snapshots per session."""

    def __init__(self):
        self._aggregates: Dict[str, SnapshotAggregate] = {}
        self._lock = threading.Lock()

    def save_aggregate(self, aggregate: SnapshotAggregate) -> None:
        with self._lock:
            self._aggregates[aggregate.session_id] = aggregate

    def get_aggregate(self, session_id: str) -> Optional[SnapshotAggregate]:
        with self._lock:
            return self._aggregates.get(session_id)
