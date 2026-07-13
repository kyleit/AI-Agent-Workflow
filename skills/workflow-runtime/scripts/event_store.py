# event_store.py
import json
import sqlite3
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

class JournalCorruptedError(Exception):
    pass

class SQLiteEventStore:
    def __init__(self, workspace_root: str = ".") -> None:
        self.db_path = os.path.join(workspace_root, ".agents", "state", "session_journal.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            # Enable WAL mode for high concurrency
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
            """)
            conn.commit()
        finally:
            conn.close()

    def append_event(self, session_id: str, topic: str, payload: Dict[str, Any]) -> None:
        import uuid
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().astimezone().isoformat()
        payload_str = json.dumps(payload)

        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO events (event_id, session_id, timestamp, topic, payload) VALUES (?, ?, ?, ?, ?)",
                (event_id, session_id, timestamp, topic, payload_str)
            )
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            raise IOError(f"Failed to append event atomic: {e}")
        finally:
            conn.close()

    def get_events(self, session_id: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT event_id, timestamp, topic, payload FROM events WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,)
            )
            rows = cursor.fetchall()
            
            events = []
            for r in rows:
                try:
                    events.append({
                        "event_id": r[0],
                        "timestamp": r[1],
                        "topic": r[2],
                        "payload": json.loads(r[3])
                    })
                except Exception as e:
                    raise JournalCorruptedError(f"Corrupted payload detected: {e}")
            return events
        finally:
            conn.close()
            
    def clear_session_events(self, session_id: str) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("DELETE FROM events WHERE session_id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()
