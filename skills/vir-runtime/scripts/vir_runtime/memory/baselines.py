# File path: vir_runtime/memory/baselines.py
import sqlite3
import time
from typing import Optional
from vir_runtime.sensory.vision.pixel_comparer import PixelComparer

class BaselineManager:
    def __init__(self, db_path: str = "vir_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vir_baselines (
                    feature_id TEXT,
                    route TEXT,
                    viewport TEXT,
                    data BLOB,
                    updated_at REAL,
                    PRIMARY KEY (feature_id, route, viewport)
                );
            """)
        conn.close()

    def get_active_baseline(self, feature_id: str, route: str, viewport: str) -> Optional[bytes]:
        """Store and query visual baselines by feature routes and breakpoints."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data FROM vir_baselines 
            WHERE feature_id = ? AND route = ? AND viewport = ?;
        """, (feature_id, route, viewport))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def check_regression(self, current_png: bytes, baseline_png: bytes) -> str:
        """Classify regression states ratios and enforce verification blocks."""
        # Wrap into standard pixel comparison logic
        comparer = PixelComparer()
        try:
            diff_ratio, _ = comparer.compare(current_png, baseline_png)
            if diff_ratio > 0.01:
                return f"REGRESSION: {diff_ratio:.2%}"
            return "MATCH"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def promote_new_baseline(self, feature_id: str, route: str, viewport: str, data: bytes) -> None:
        """Promote new visual findings as active baseline."""
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO vir_baselines (feature_id, route, viewport, data, updated_at)
                VALUES (?, ?, ?, ?, ?);
            """, (feature_id, route, viewport, sqlite3.Binary(data), time.time()))
        conn.close()
        print(f"[BaselineManager] Promoted new baseline for {feature_id} on {route} ({viewport})")
    
    def clear_expired_baselines(self, expired_timestamp: float) -> None:
        """Clean old baselines metadata to control database growth limits."""
        conn = sqlite3.connect(self.db_path)
        with conn:
            conn.execute("DELETE FROM vir_baselines WHERE updated_at < ?;", (expired_timestamp,))
        conn.close()
