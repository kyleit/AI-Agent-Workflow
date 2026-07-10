import os
import sqlite3
import warnings
from .base import BaseProvider

class SQLiteProvider(BaseProvider):
    def __init__(self, db_path: str = ".agents/state/knowledge.db", workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.db_path = os.path.abspath(os.path.join(self.workspace_root, db_path))
        self._initialized = False
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._init_db()
            self._initialized = True
        except Exception as e:
            warnings.warn(f"SQLiteProvider failed to initialize: {e}. Falling back to markdown.")

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                expires_at INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backlinks (
                source TEXT,
                target TEXT,
                PRIMARY KEY (source, target)
            )
        """)
        conn.commit()
        conn.close()

    def search(self, query: str, limit: int = 5) -> list[dict]:
        if not self._initialized:
            return []
        
        results = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Simple fallback search using backlinks mapping or cache content match
            cursor.execute("SELECT source, target FROM backlinks WHERE target LIKE ?", (f"%{query}%",))
            rows = cursor.fetchall()
            for r in rows:
                results.append({
                    "path": r[0],
                    "snippet": f"Linked to {r[1]}",
                    "score": 0.8
                })
            conn.close()
        except Exception as e:
            warnings.warn(f"SQLite search failed: {e}")
            
        return results[:limit]

    def read(self, path: str) -> str:
        # Relies on markdown provider for reading files
        raise NotImplementedError("Use MarkdownProvider for file reading.")

    def save(self, path: str, content: str) -> bool:
        # Relies on markdown provider for saving files
        return False

    def is_available(self) -> bool:
        return self._initialized
