# event_bus.py
# RuntimeEventBus — SQLite-backed emit/subscribe/replay for FEAT-048 Phase 4
# Per ADR-005: Phase 1 = SQLite Journal; Phase 2 = WebSocket opt-in (FEAT-049)
from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RuntimeEvent dataclass
# ---------------------------------------------------------------------------

@dataclass
class RuntimeEvent:
    """A single event emitted by any provider component."""
    event_id: str
    timestamp: str
    conversation_id: str
    provider: str
    event_type: str          # e.g. "usage_parsed", "transcript_read", "diagnostics_refreshed"
    event_data: dict = field(default_factory=dict)

    def __post_init__(self):
        # Validate required fields
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not isinstance(self.event_data, dict):
            self.event_data = {}

    @classmethod
    def create(
        cls,
        conversation_id: str,
        provider: str,
        event_type: str,
        event_data: dict = None,
    ) -> "RuntimeEvent":
        """Factory — creates a new event with auto-generated id and timestamp."""
        return cls(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id=conversation_id,
            provider=provider,
            event_type=event_type,
            event_data=event_data or {},
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "conversation_id": self.conversation_id,
            "provider": self.provider,
            "event_type": self.event_type,
            "event_data": self.event_data,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "RuntimeEvent":
        """Reconstruct from SQLite row (id, event_id, timestamp, conv_id, provider, event_type, event_data_json)."""
        _, event_id, timestamp, conversation_id, provider, event_type, event_data_json = row
        try:
            event_data = json.loads(event_data_json)
        except (json.JSONDecodeError, TypeError):
            event_data = {}
        return cls(
            event_id=event_id,
            timestamp=timestamp,
            conversation_id=conversation_id,
            provider=provider,
            event_type=event_type,
            event_data=event_data,
        )


# ---------------------------------------------------------------------------
# RuntimeEventBus
# ---------------------------------------------------------------------------

class RuntimeEventBus:
    """
    SQLite-backed event bus for provider runtime events.

    Per ADR-005:
    - Phase 1: All events persisted to SQLite runtime_events table.
    - Phase 2 (FEAT-049): Optional WebSocket fan-out added as opt-in layer.

    Thread safety: Uses SQLite WAL mode + check_same_thread=False.
    Transaction safety: Each emit() is a single committed transaction.
    """

    def __init__(self, db_conn: sqlite3.Connection):
        """
        Args:
            db_conn: Active SQLite connection. Must have runtime_events table
                     (created by db.init_db_schema()).
        """
        self._conn = db_conn
        self._handlers: dict[str, list[Callable]] = defaultdict(list)
        self._ensure_table()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def emit(self, event: RuntimeEvent) -> None:
        """
        Persist event to SQLite and invoke all registered handlers.

        Args:
            event: RuntimeEvent to persist and dispatch.

        Raises:
            Never — all errors are caught and logged as WARNING.
        """
        try:
            self._persist(event)
        except Exception as exc:
            logger.warning("EventBus: Failed to persist event %s: %s", event.event_id, exc)

        # Dispatch to in-process subscribers
        handlers = self._handlers.get(event.event_type, []) + self._handlers.get("*", [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.warning("EventBus: Handler error for %s: %s", event.event_type, exc)

    def subscribe(self, event_type: str, handler: Callable[[RuntimeEvent], None]) -> None:
        """
        Register an in-process handler for a given event_type.

        Args:
            event_type: Event type string to subscribe to. Use "*" to receive all events.
            handler: Callable accepting a single RuntimeEvent argument.
        """
        self._handlers[event_type].append(handler)
        logger.debug("EventBus: Subscribed handler %s to '%s'", handler.__name__, event_type)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Remove a previously registered handler."""
        try:
            self._handlers[event_type].remove(handler)
        except (KeyError, ValueError):
            pass

    def replay(
        self,
        conversation_id: str,
        since: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 500,
    ) -> List[RuntimeEvent]:
        """
        Retrieve persisted events from SQLite for a given conversation.

        Args:
            conversation_id: Filter by conversation ID.
            since: ISO8601 timestamp — return only events after this time.
            event_type: Optional filter by event_type.
            limit: Maximum number of events to return (default: 500).

        Returns:
            List of RuntimeEvent ordered by timestamp ASC.
        """
        try:
            query = "SELECT * FROM runtime_events WHERE conversation_id = ?"
            params: list = [conversation_id]

            if since:
                query += " AND timestamp > ?"
                params.append(since)

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            query += " ORDER BY timestamp ASC LIMIT ?"
            params.append(limit)

            rows = self._conn.execute(query, params).fetchall()
            return [RuntimeEvent.from_row(row) for row in rows]
        except Exception as exc:
            logger.warning("EventBus: replay() failed for conv %s: %s", conversation_id, exc)
            return []

    def get_event_count(self, conversation_id: str) -> int:
        """Return total number of events for a conversation."""
        try:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM runtime_events WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchone()
            return row[0] if row else 0
        except Exception:
            return 0

    def prune_old_events(self, older_than_days: int = 30) -> int:
        """
        Delete events older than N days. Per blueprint maintenance strategy.

        Returns:
            Number of rows deleted.
        """
        try:
            from datetime import timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
            with self._conn:
                cursor = self._conn.execute(
                    "DELETE FROM runtime_events WHERE timestamp < ?", (cutoff,)
                )
            deleted = cursor.rowcount
            logger.info("EventBus: Pruned %d events older than %d days", deleted, older_than_days)
            return deleted
        except Exception as exc:
            logger.warning("EventBus: prune_old_events() failed: %s", exc)
            return 0

    def clear_handlers(self) -> None:
        """Remove all in-process subscribers (useful for testing)."""
        self._handlers.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _persist(self, event: RuntimeEvent) -> None:
        """Write event to SQLite runtime_events in a single transaction."""
        event_data_json = json.dumps(event.event_data, ensure_ascii=False)
        with self._conn:
            self._conn.execute(
                """
                INSERT OR IGNORE INTO runtime_events
                    (event_id, timestamp, conversation_id, provider, event_type, event_data_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.timestamp,
                    event.conversation_id,
                    event.provider,
                    event.event_type,
                    event_data_json,
                ),
            )

    def _ensure_table(self) -> None:
        """Ensure runtime_events table exists (safety net if db.init_db_schema not called)."""
        try:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runtime_events (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id        TEXT NOT NULL UNIQUE,
                    timestamp       TEXT NOT NULL,
                    conversation_id TEXT NOT NULL,
                    provider        TEXT NOT NULL,
                    event_type      TEXT NOT NULL,
                    event_data_json TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_runtime_events_conv ON runtime_events (conversation_id)"
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_runtime_events_type ON runtime_events (event_type)"
            )
            self._conn.commit()
        except Exception as exc:
            logger.debug("EventBus: _ensure_table skipped: %s", exc)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_event_bus(db_conn: sqlite3.Connection) -> RuntimeEventBus:
    """
    Create a RuntimeEventBus bound to the given SQLite connection.

    Args:
        db_conn: Open SQLite connection with runtime_events table.

    Returns:
        Ready-to-use RuntimeEventBus instance.
    """
    return RuntimeEventBus(db_conn=db_conn)
