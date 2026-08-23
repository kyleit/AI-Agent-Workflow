# File path: vir_runtime/core/runtime.py
from __future__ import annotations

import os
import sqlite3
from typing import Any

import yaml


class VIRRuntimeCore:
    def __init__(self, config_path: str = "config.yaml", db_path: str = "vir_state.db") -> None:
        self.config_path = config_path
        self.db_path = db_path
        self.config: dict[str, Any] = {}
        self.db_conn: sqlite3.Connection | None = None

    def bootstrap(self) -> None:
        """Initialize settings and database connections."""
        # Load configuration
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = {
                "vir": {
                    "version": "1.0.0",
                    "profile": "standard"
                }
            }

        # Initialize SQLite Database with WAL mode
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.execute("PRAGMA journal_mode=WAL;")

        # Create default tables
        with self.db_conn:
            self.db_conn.execute("""
                CREATE TABLE IF NOT EXISTS vir_session (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT,
                    status TEXT
                );
            """)

    def shutdown(self) -> None:
        """Gracefully release connections and lock files."""
        if self.db_conn is not None:
            self.db_conn.close()
            self.db_conn = None


__all__ = ["VIRRuntimeCore"]
