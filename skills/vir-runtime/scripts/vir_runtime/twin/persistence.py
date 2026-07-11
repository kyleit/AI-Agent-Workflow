# File path: vir_runtime/twin/persistence.py
import sqlite3
import json
import time
import asyncio
from typing import Dict, Any, Optional

class DigitalTwinManager:
    def __init__(self, db_path: str = "vir_state.db"):
        self.db_path = db_path
        self.lock = asyncio.Lock()
        self.in_memory_state: Dict[str, Dict[str, Any]] = {}
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vir_digital_twin (
                    dimension_name TEXT PRIMARY KEY,
                    payload TEXT,
                    updated_at TEXT
                );
            """)
        conn.close()

    async def update_dimension(self, dimension: str, value: Dict[str, Any]) -> None:
        """Synchronize application dimensions updates thread-safely."""
        async with self.lock:
            # Update cache
            self.in_memory_state[dimension] = value
            
            # Serialize to SQLite
            payload_str = json.dumps(value)
            updated_at = str(time.time())
            
            conn = sqlite3.connect(self.db_path)
            try:
                with conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO vir_digital_twin (dimension_name, payload, updated_at)
                        VALUES (?, ?, ?);
                    """, (dimension, payload_str, updated_at))
            finally:
                conn.close()

    async def get_dimension_value(self, dimension: str) -> Dict[str, Any]:
        """Query dimension value, fallback to SQLite if not in cache."""
        async with self.lock:
            if dimension in self.in_memory_state:
                return self.in_memory_state[dimension]

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT payload FROM vir_digital_twin WHERE dimension_name = ?;", (dimension,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                value = json.loads(row[0])
                self.in_memory_state[dimension] = value
                return value
            return {}
