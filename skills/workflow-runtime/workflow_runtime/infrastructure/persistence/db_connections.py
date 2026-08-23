from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
from typing import Any, cast

_orig_sqlite3_connect: Any = sqlite3.connect


def _custom_sqlite3_connect(
    database: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    *args: Any,
    **kwargs: Any
) -> sqlite3.Connection:
    mode = os.environ.get("AIWF_RUNTIME_MODE", "normal").lower()
    disable_writes = os.environ.get("AIWF_DISABLE_STATE_WRITES", "false").lower() == "true"
    if disable_writes or mode in ["test-memory", "test-isolated"]:
        return cast(sqlite3.Connection, _orig_sqlite3_connect(":memory:", *args, **kwargs))

    if "timeout" not in kwargs:
        kwargs["timeout"] = 5.0
    conn = cast(sqlite3.Connection, _orig_sqlite3_connect(database, *args, **kwargs))
    if str(database) != ":memory:":
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            row = cursor.fetchone()
            current_mode = str(row[0]).lower() if row and len(row) > 0 else ""
            if current_mode != "wal":
                conn.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
    return conn


sqlite3.connect = _custom_sqlite3_connect  # type: ignore[assignment]


def get_project_db_path() -> str:
    project_id = "ai-skill-framework"
    config_path = os.path.join(".agents", "memory.config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
                project_id = str(data.get("project_id", "ai-skill-framework"))
        except Exception:
            pass
    new_db = os.path.join(".agents", "state", f"{project_id}.db")
    old_db = os.path.join(".agents", "project_runtime.db")

    os.makedirs(os.path.dirname(new_db), exist_ok=True)

    if os.path.exists(old_db) and not os.path.exists(new_db):
        try:
            shutil.move(old_db, new_db)
        except Exception:
            try:
                shutil.copy2(old_db, new_db)
            except Exception:
                return old_db

    if os.path.exists(new_db):
        return new_db
    return old_db


PROJECT_DB = get_project_db_path()


def connect_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30.0)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
    except Exception:
        pass
    return conn


def get_global_db_path() -> str:
    if sys.platform.startswith("win"):
        base = os.getenv("APPDATA") or os.path.expanduser("~/AppData/Roaming")
        folder = os.path.join(base, "AI Workflow")
    elif sys.platform.startswith("darwin"):
        folder = os.path.expanduser("~/Library/Application Support/AI Workflow")
    else:
        folder = os.path.expanduser("~/.config/ai-workflow")

    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "global_runtime.db")


_INITIALIZED_DBS: set[str] = set()
_schemas_initialized: set[str] = set()


__all__ = [
    "PROJECT_DB",
    "get_project_db_path",
    "connect_db",
    "get_global_db_path",
]
