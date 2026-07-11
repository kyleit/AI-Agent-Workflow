# execution_queue_checkpoint.py
import sqlite3
import os
import json
import time

class ExecutionQueueCheckpointManager:
    """
    FEAT-086 & FEAT-087 Upgrade: Execution Queue + Checkpoint & Resume
    Provides persistence for execution queues and task checkpoints.
    """
    def __init__(self, db_path: str = ".agents/runtime/execution_queue.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS queue (
                    queue_id TEXT PRIMARY KEY,
                    objective_id TEXT,
                    program_id TEXT,
                    sprint_id TEXT,
                    feat_id TEXT,
                    priority INTEGER,
                    status TEXT,
                    node TEXT,
                    retry_count INTEGER,
                    owner TEXT,
                    created_time REAL
                );
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_key TEXT PRIMARY KEY,
                    data TEXT,
                    updated_time REAL
                );
            """)
            conn.commit()
        finally:
            conn.close()

    def enqueue(self, item: dict) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO queue VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                item.get("queue_id"),
                item.get("objective_id"),
                item.get("program_id"),
                item.get("sprint_id"),
                item.get("feat_id"),
                item.get("priority", 0),
                item.get("status", "READY"),
                item.get("node", "local"),
                item.get("retry_count", 0),
                item.get("owner", "System"),
                time.time()
            ))
            conn.commit()
        finally:
            conn.close()

    def dequeue(self) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT queue_id, objective_id, program_id, sprint_id, feat_id, priority, status, node, retry_count, owner 
                FROM queue WHERE status = 'READY' ORDER BY priority DESC, created_time ASC LIMIT 1;
            """)
            row = cursor.fetchone()
            if row:
                conn.execute("UPDATE queue SET status = 'RUNNING' WHERE queue_id = ?;", (row[0],))
                conn.commit()
                return {
                    "queue_id": row[0],
                    "objective_id": row[1],
                    "program_id": row[2],
                    "sprint_id": row[3],
                    "feat_id": row[4],
                    "priority": row[5],
                    "status": "RUNNING",
                    "node": row[6],
                    "retry_count": row[7],
                    "owner": row[8]
                }
            return None
        finally:
            conn.close()

    def save_checkpoint(self, key: str, data: dict) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO checkpoints VALUES (?, ?, ?);
            """, (key, json.dumps(data), time.time()))
            conn.commit()
        finally:
            conn.close()

    def load_checkpoint(self, key: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM checkpoints WHERE checkpoint_key = ?;", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
        finally:
            conn.close()
