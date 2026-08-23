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
from typing import Any, Callable, cast

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
    event_data: dict[str, Any] = field(default_factory=dict[str, Any])

    def __post_init__(self) -> None:
        # Validate required fields
        if not self.event_id:
            self.event_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    @classmethod
    def create(
        cls,
        conversation_id: str,
        provider: str,
        event_type: str,
        event_data: dict[str, Any] | None = None,
    ) -> RuntimeEvent:
        """Factory — creates a new event with auto-generated id and timestamp."""
        return cls(
            event_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id=conversation_id,
            provider=provider,
            event_type=event_type,
            event_data=event_data if event_data is not None else {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "conversation_id": self.conversation_id,
            "provider": self.provider,
            "event_type": self.event_type,
            "event_data": self.event_data,
        }

    @classmethod
    def from_row(cls, row: tuple[Any, ...]) -> RuntimeEvent:
        """Reconstruct from SQLite row (id, event_id, timestamp, conv_id, provider, event_type, event_data_json)."""
        _, event_id, timestamp, conversation_id, provider, event_type, event_data_json = row
        try:
            event_data = cast(dict[str, Any], json.loads(str(event_data_json)))
        except (json.JSONDecodeError, TypeError):
            event_data = {}
        return cls(
            event_id=str(event_id),
            timestamp=str(timestamp),
            conversation_id=str(conversation_id),
            provider=str(provider),
            event_type=str(event_type),
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

    def __init__(self, db_conn: sqlite3.Connection) -> None:
        self._conn = db_conn
        self._handlers: dict[str, list[Callable[[RuntimeEvent], None]]] = defaultdict(list)
        self._ensure_table()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def emit(self, event: RuntimeEvent) -> None:
        """
        Persist event to SQLite and invoke all registered handlers.
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
        """
        self._handlers[event_type].append(handler)
        func_name = getattr(handler, "__name__", str(handler))
        logger.debug("EventBus: Subscribed handler %s to '%s'", func_name, event_type)

    def unsubscribe(self, event_type: str, handler: Callable[[RuntimeEvent], None]) -> None:
        """Remove a previously registered handler."""
        try:
            self._handlers[event_type].remove(handler)
        except (KeyError, ValueError):
            pass

    def replay(
        self,
        conversation_id: str,
        since: str | None = None,
        event_type: str | None = None,
        limit: int = 500,
    ) -> list[RuntimeEvent]:
        """
        Retrieve persisted events from SQLite for a given conversation.
        """
        try:
            query = "SELECT * FROM runtime_events WHERE conversation_id = ?"
            params: list[Any] = [conversation_id]

            if since:
                query += " AND timestamp > ?"
                params.append(since)

            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)

            query += " ORDER BY timestamp ASC LIMIT ?"
            params.append(limit)

            rows = cast(list[tuple[Any, ...]], self._conn.execute(query, params).fetchall())
            return [RuntimeEvent.from_row(row) for row in rows]
        except Exception as exc:
            logger.warning("EventBus: replay() failed for conv %s: %s", conversation_id, exc)
            return []

    def get_event_count(self, conversation_id: str) -> int:
        """Return total number of events for a conversation."""
        try:
            row = cast(tuple[Any, ...] | None, self._conn.execute(
                "SELECT COUNT(*) FROM runtime_events WHERE conversation_id = ?",
                (conversation_id,)
            ).fetchone())
            return int(row[0]) if row and len(row) > 0 else 0
        except Exception:
            return 0

    def prune_old_events(self, older_than_days: int = 30) -> int:
        """
        Delete events older than N days. Per blueprint maintenance strategy.
        """
        try:
            from datetime import timedelta
            cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat()
            with self._conn:
                cursor = self._conn.execute(
                    "DELETE FROM runtime_events WHERE timestamp < ?", (cutoff,)
                )
            deleted = int(cursor.rowcount)
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


def build_event_bus(db_conn: sqlite3.Connection) -> RuntimeEventBus:
    """
    Create a RuntimeEventBus bound to the given SQLite connection.
    """
    return RuntimeEventBus(db_conn=db_conn)


__all__ = [
    "RuntimeEvent",
    "RuntimeEventBus",
    "build_event_bus",
]
