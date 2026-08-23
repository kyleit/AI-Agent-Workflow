from __future__ import annotations

from typing import Protocol

"""DIP Port for Usage Record persistence.

Application layer declares this interface.
Infrastructure layer (db_records.py) provides the concrete implementation.
Composition Root wires the two together at startup.

Verified from:
  - infrastructure/persistence/db_records.py:L337 — def save_insight_snapshot(snapshot: dict) -> None
  - application/ports/locator.py:L4 — class-based port pattern already used in project
"""


class UsageRecordPort(Protocol):
    """Port for persisting usage insight snapshots.

    Conforming implementations must accept a snapshot dict and persist it
    to durable storage without raising on partial data.
    """

    def save_insight_snapshot(self, snapshot: dict[str, object]) -> None:
        """Persist one usage insight snapshot to durable storage."""
        ...