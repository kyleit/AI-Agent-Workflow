# node_agent_registry.py
import sqlite3
import os

class NodeAgentRegistry:
    """
    FEAT-109: Distributed Runtime Platform
    Node Agent Registry persistence implementation via SQLite.
    """
    def __init__(self, db_path: str = ".agents/runtime/nodes.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS active_nodes (
                    worker_id TEXT PRIMARY KEY,
                    capacity INTEGER,
                    status TEXT
                );
            """)
            conn.commit()
        finally:
            conn.close()

    def register_worker(self, worker_id: str, capacity: int) -> bool:
        # Prevent path traversal characters in worker ID
        if "../" in worker_id or "..\\" in worker_id:
            return False
            
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO active_nodes VALUES (?, ?, 'ACTIVE');",
                (worker_id, capacity)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()
