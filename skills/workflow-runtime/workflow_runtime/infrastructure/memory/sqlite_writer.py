from __future__ import annotations
# sqlite_writer.py
import os
import sqlite3

from .common import get_project_root


def init_sqlite_indexes(db_path: str | None = None) -> bool:
    if not db_path:
        db_path = os.path.join(get_project_root(), ".agents", "project_runtime.db")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Tạo bảng lưu vết các file đã chỉ mục
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indexed_files (
                filepath TEXT PRIMARY KEY,
                target_doc TEXT,
                last_indexed_at TEXT
            )
        """)
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False


def populate_indexed_files(file_map: dict[str, str], db_path: str | None = None) -> int:
    if not db_path:
        db_path = os.path.join(get_project_root(), ".agents", "project_runtime.db")
    init_sqlite_indexes(db_path)
    from datetime import datetime
    now_iso = datetime.now().astimezone().isoformat()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        for filepath, target_doc in file_map.items():
            cursor.execute("""
                INSERT OR REPLACE INTO indexed_files (filepath, target_doc, last_indexed_at)
                VALUES (?, ?, ?)
            """, (filepath, target_doc, now_iso))
        conn.commit()
        count = len(file_map)
        conn.close()
        return count
    except Exception:
        return 0


__all__ = ["init_sqlite_indexes", "populate_indexed_files"]
