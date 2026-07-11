# File path: vir_runtime/multi_agent/memory.py
import sqlite3
import json
import time
from typing import Any, Dict

class AgentMemory:
    def __init__(self, agent_id: str, db_path: str = "vir_state.db"):
        self.agent_id = agent_id
        self.db_path = db_path
        self.short_term: Dict[str, Any] = {}
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vir_agent_memory (
                    agent_id TEXT,
                    key TEXT,
                    value TEXT,
                    updated_at TEXT,
                    PRIMARY KEY (agent_id, key)
                );
            """)
        conn.close()

    def write_short_term(self, key: str, value: Any) -> None:
        """Expose short term memory in RAM dict cache."""
        self.short_term[key] = value

    def save_long_term(self, key: str, value: Any) -> None:
        """Serialize long term memories into SQLite metadata tables."""
        conn = sqlite3.connect(self.db_path)
        val_str = json.dumps(value)
        updated_at = str(time.time())
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO vir_agent_memory (agent_id, key, value, updated_at)
                VALUES (?, ?, ?, ?);
            """, (self.agent_id, key, val_str, updated_at))
        conn.close()
