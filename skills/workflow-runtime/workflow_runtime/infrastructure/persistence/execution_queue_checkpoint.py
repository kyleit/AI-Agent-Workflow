from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any, cast


class ExecutionQueueCheckpointManager:
    """
    FEAT-086 & FEAT-087 Upgrade: Execution Queue + Checkpoint & Resume
    Provides persistence for execution queues and task checkpoints.
    """
    def __init__(self, db_path: str = ".agents/runtime/execution_queue.db") -> None:
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

    def enqueue(self, item: dict[str, Any]) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            raw_qid = item.get("queue_id")
            qid_val = str(raw_qid) if raw_qid is not None else None
            raw_obj = item.get("objective_id")
            obj_val = str(raw_obj) if raw_obj is not None else None
            raw_prog = item.get("program_id")
            prog_val = str(raw_prog) if raw_prog is not None else None
            raw_sprint = item.get("sprint_id")
            sprint_val = str(raw_sprint) if raw_sprint is not None else None
            raw_feat = item.get("feat_id")
            feat_val = str(raw_feat) if raw_feat is not None else None

            prio_val = int(str(item.get("priority", 0)))
            status_val = str(item.get("status", "READY"))
            node_val = str(item.get("node", "local"))
            retry_val = int(str(item.get("retry_count", 0)))
            owner_val = str(item.get("owner", "System"))
            now_time = float(time.time())

            conn.execute("""
                INSERT OR REPLACE INTO queue VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                qid_val,
                obj_val,
                prog_val,
                sprint_val,
                feat_val,
                prio_val,
                status_val,
                node_val,
                retry_val,
                owner_val,
                now_time,
            ))
            conn.commit()
        finally:
            conn.close()

    def dequeue(self) -> dict[str, Any] | None:
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
                    "queue_id": str(row[0]),
                    "objective_id": str(row[1]),
                    "program_id": str(row[2]),
                    "sprint_id": str(row[3]),
                    "feat_id": str(row[4]),
                    "priority": int(row[5]),
                    "status": "RUNNING",
                    "node": str(row[7]),
                    "retry_count": int(row[8]),
                    "owner": str(row[9])
                }
            return None
        finally:
            conn.close()

    def save_checkpoint(self, key: str, data: dict[str, Any]) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT OR REPLACE INTO checkpoints VALUES (?, ?, ?);
            """, (key, json.dumps(data), time.time()))
            conn.commit()
        finally:
            conn.close()

    def load_checkpoint(self, key: str) -> dict[str, Any] | None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM checkpoints WHERE checkpoint_key = ?;", (key,))
            row = cursor.fetchone()
            if row:
                parsed = cast(dict[str, Any], json.loads(str(row[0])))
                return parsed
            return None
        finally:
            conn.close()


__all__ = ["ExecutionQueueCheckpointManager"]
