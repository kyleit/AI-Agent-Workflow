# sqlite_writer.py
import sqlite3
import os
from common import get_project_root

def init_sqlite_indexes(db_path: str = None) -> bool:
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
