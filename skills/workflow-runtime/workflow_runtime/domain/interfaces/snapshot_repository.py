from typing import Optional, Protocol

from workflow_runtime.domain.models.snapshot_aggregate import SnapshotAggregate


class ISnapshotRepository(Protocol):
    def save_aggregate(self, aggregate: SnapshotAggregate) -> None:
        """Persists or updates a SnapshotAggregate instance."""
        ...

    def get_aggregate(self, session_id: str) -> Optional[SnapshotAggregate]:
        """Retrieves SnapshotAggregate by session ID."""
        ...
