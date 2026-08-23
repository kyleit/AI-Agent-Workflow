"""
workflow_runtime/infrastructure/persistence/timeline_event_records.py

Database records adapter for timeline events logging and querying.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from workflow_runtime.infrastructure.persistence.db_connections import (
    PROJECT_DB, connect_db, get_global_db_path)
from workflow_runtime.infrastructure.persistence.db_schema import (
    init_db_schema)


def save_timeline_event(event: dict[str, Any]) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = connect_db(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()

            if event.get("request_id"):
                cursor.execute(
                    "SELECT 1 FROM timeline_events WHERE request_id = ? AND event_type = ?",
                    (event["request_id"], event.get("event_type", "Provider request"))
                )
                if cursor.fetchone():
                    continue

            details_json = event.get("details")
            if isinstance(details_json, (dict, list)):
                details_json = json.dumps(details_json)

            record = (
                event.get("timestamp") or datetime.now().astimezone().isoformat(),
                event.get("conversation_id"),
                event.get("event_type"),
                event.get("checkpoint", 1),
                event.get("skill") or "unknown",
                event.get("request_id"),
                event.get("active_context", 0),
                event.get("context_delta", 0),
                event.get("input_tokens", 0),
                event.get("output_tokens", 0),
                event.get("cost", 0.0),
                event.get("duration", 0.0),
                details_json or "{}"
            )

            cursor.execute("""
                INSERT INTO timeline_events (
                    timestamp, conversation_id, event_type, checkpoint, skill,
                    request_id, active_context, context_delta, input_tokens,
                    output_tokens, cost, duration, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()
        finally:
            conn.close()


def get_timeline_events(conversation_id: str) -> list[dict[str, Any]]:
    if not os.path.exists(PROJECT_DB):
        return []
    conn = connect_db(PROJECT_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, conversation_id, event_type, checkpoint, skill,
                   request_id, active_context, context_delta, input_tokens,
                   output_tokens, cost, duration, details_json
            FROM timeline_events
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """, (conversation_id,))
        rows = cursor.fetchall()
        results: list[dict[str, Any]] = []
        for r in rows:
            try:
                details = json.loads(r[13])
            except Exception:
                details = {}
            results.append({
                "id": r[0],
                "timestamp": r[1],
                "conversation_id": r[2],
                "event_type": r[3],
                "checkpoint": r[4],
                "skill": r[5],
                "request_id": r[6],
                "active_context": r[7],
                "context_delta": r[8],
                "input_tokens": r[9],
                "output_tokens": r[10],
                "cost": r[11],
                "duration": r[12],
                "details": details
            })
        return results
    finally:
        conn.close()


__all__ = [
    "save_timeline_event",
    "get_timeline_events",
]
