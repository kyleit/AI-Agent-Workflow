# db.py
import os
import sqlite3
import sys
from datetime import datetime

PROJECT_DB = os.path.join(".agents", "project_runtime.db")

def get_global_db_path() -> str:
    # Determine OS AppData path
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA") or os.path.expanduser("~/AppData/Roaming")
        folder = os.path.join(base, "AI Workflow")
    elif sys.platform.startswith("darwin"):
        folder = os.path.expanduser("~/Library/Application Support/AI Workflow")
    else:
        # Linux / other
        folder = os.path.expanduser("~/.config/ai-workflow")
    
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "global_runtime.db")

def _save_record(db_path: str, record: tuple) -> None:
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_records (
                conversation_id TEXT PRIMARY KEY,
                project_id TEXT,
                skill TEXT,
                command TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cache_tokens INTEGER,
                thinking_tokens INTEGER,
                active_tokens INTEGER,
                total_tokens INTEGER,
                estimated_cost_usd REAL,
                provider TEXT,
                model TEXT,
                accuracy TEXT,
                timestamp TEXT
            )
        """)
        # Migrating existing table if column active_tokens is missing
        try:
            cursor.execute("SELECT active_tokens FROM usage_records LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("ALTER TABLE usage_records ADD COLUMN active_tokens INTEGER DEFAULT 0")
            conn.commit()

        cursor.execute("""
            INSERT OR REPLACE INTO usage_records (
                conversation_id, project_id, skill, command,
                input_tokens, output_tokens, cache_tokens, thinking_tokens, active_tokens, total_tokens,
                estimated_cost_usd, provider, model, accuracy, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, record)
        conn.commit()
    finally:
        conn.close()

def save_usage_to_dbs(conversation_id: str, project_id: str, skill: str, command: str, usage: dict) -> None:
    record = (
        conversation_id,
        project_id,
        skill,
        command,
        usage.get("input_tokens", 0),
        usage.get("output_tokens", 0),
        usage.get("cache_tokens", 0),
        usage.get("thinking_tokens", 0),
        usage.get("active_tokens", 0),
        usage.get("total_tokens", 0),
        usage.get("estimated_cost_usd", 0.0),
        usage.get("provider", "unknown"),
        usage.get("model", "unknown"),
        usage.get("accuracy", "unknown"),
        datetime.now().astimezone().isoformat()
    )
    
    # Save to Project DB
    _save_record(PROJECT_DB, record)
    
    # Save to Global DB
    global_db = get_global_db_path()
    _save_record(global_db, record)

def get_workflow_summary(conversation_id: str, provider: str, model: str) -> dict:
    conn = sqlite3.connect(PROJECT_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT input_tokens, output_tokens, cache_tokens, thinking_tokens, active_tokens, total_tokens,
                   estimated_cost_usd, provider, model, accuracy, timestamp
            FROM usage_records WHERE conversation_id = ?
        """, (conversation_id,))
        row = cursor.fetchone()
        if row:
            active_tokens = row[4]
            return {
                "provider": row[7],
                "model": row[8],
                "input_tokens": row[0],
                "output_tokens": row[1],
                "cache_tokens": row[2],
                "thinking_tokens": row[3],
                "active_tokens": active_tokens,
                "total_tokens": row[5],
                "limit_tokens": 2000000,
                "percentage": round((active_tokens / 2000000) * 100, 2),
                "estimated_cost_usd": row[6],
                "accuracy": row[9],
                "updated_at": row[10]
            }
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    
    # Fallback default if not found
    return {
        "provider": provider,
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "active_tokens": 0,
        "total_tokens": 0,
        "limit_tokens": 2000000,
        "percentage": 0.0,
        "estimated_cost_usd": 0.0,
        "accuracy": "estimated",
        "updated_at": datetime.now().astimezone().isoformat()
    }

def get_project_summary() -> dict:
    conn = sqlite3.connect(PROJECT_DB)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
                   SUM(thinking_tokens), SUM(total_tokens), SUM(estimated_cost_usd)
            FROM usage_records
        """)
        row = cursor.fetchone()
        if row and row[4] is not None:
            return {
                "input_tokens": row[0],
                "output_tokens": row[1],
                "cache_tokens": row[2],
                "thinking_tokens": row[3],
                "total_tokens": row[4],
                "estimated_cost_usd": round(row[5], 4),
                "updated_at": datetime.now().astimezone().isoformat()
            }
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "updated_at": datetime.now().astimezone().isoformat()
    }

def get_global_summary() -> dict:
    global_db = get_global_db_path()
    conn = sqlite3.connect(global_db)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
                   SUM(thinking_tokens), SUM(total_tokens), SUM(estimated_cost_usd)
            FROM usage_records
        """)
        row = cursor.fetchone()
        if row and row[4] is not None:
            return {
                "input_tokens": row[0],
                "output_tokens": row[1],
                "cache_tokens": row[2],
                "thinking_tokens": row[3],
                "total_tokens": row[4],
                "estimated_cost_usd": round(row[5], 4),
                "updated_at": datetime.now().astimezone().isoformat()
            }
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "updated_at": datetime.now().astimezone().isoformat()
    }
