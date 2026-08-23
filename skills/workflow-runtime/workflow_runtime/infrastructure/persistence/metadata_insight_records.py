"""
workflow_runtime/infrastructure/persistence/metadata_insight_records.py

Global summary, database record normalizer, and QMD metadata persistence.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Any

from workflow_runtime.infrastructure.persistence.db_connections import (
    PROJECT_DB, connect_db, get_global_db_path, get_project_db_path)
from workflow_runtime.infrastructure.persistence.db_schema import (
    init_db_schema)


def get_global_summary() -> dict[str, Any]:
    global_db = get_global_db_path()
    fallback = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "updated_at": datetime.now().astimezone().isoformat()
    }
    if not os.path.exists(global_db):
        return fallback

    conn = None
    try:
        conn = connect_db(global_db)
        cursor = conn.cursor()

        has_requests = False
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provider_requests'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM provider_requests")
            if cursor.fetchone()[0] > 0:
                has_requests = True

        if not has_requests:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
                           SUM(thinking_tokens), SUM(total_tokens), SUM(estimated_cost_usd)
                    FROM usage_records
                """)
                row = cursor.fetchone()
                if row and row[4] is not None:
                    return {
                        "input_tokens": row[0] or 0,
                        "output_tokens": row[1] or 0,
                        "cache_tokens": row[2] or 0,
                        "thinking_tokens": row[3] or 0,
                        "total_tokens": row[4] or 0,
                        "estimated_cost_usd": round(row[5] or 0.0, 4),
                        "updated_at": datetime.now().astimezone().isoformat()
                    }
            return fallback

        cursor.execute("""
            SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
                   SUM(thinking_tokens), SUM(total_tokens), SUM(cost_usd)
            FROM provider_requests
        """)
        row = cursor.fetchone()
        if row and row[4] is not None:
            return {
                "input_tokens": row[0] or 0,
                "output_tokens": row[1] or 0,
                "cache_tokens": row[2] or 0,
                "thinking_tokens": row[3] or 0,
                "total_tokens": row[4] or 0,
                "estimated_cost_usd": round(row[5] or 0.0, 4),
                "updated_at": datetime.now().astimezone().isoformat()
            }
    except Exception:
        pass
    finally:
        if conn:
            conn.close()
    return fallback


def normalize_database_records(db_path: str) -> None:
    if not os.path.exists(db_path):
        return
    from workflow_runtime.domain.core.context import parse_transcript
    conn = connect_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'")
        if not cursor.fetchone():
            return

        cursor.execute("SELECT conversation_id, total_tokens FROM usage_records")
        rows = cursor.fetchall()
        for conv_id, _total_tok in rows:
            home = os.path.expanduser("~")
            log_path = os.path.join(home, ".gemini", "antigravity-ide", "brain", conv_id, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(log_path):
                usage = parse_transcript(log_path)
                if usage:
                    cursor.execute("""
                        UPDATE usage_records
                        SET input_tokens = ?, output_tokens = ?, cache_tokens = ?,
                            thinking_tokens = ?, active_tokens = ?, total_tokens = ?,
                            estimated_cost_usd = ?
                        WHERE conversation_id = ?
                    """, (
                        usage.get("input_tokens", 0),
                        usage.get("output_tokens", 0),
                        usage.get("cache_tokens", 0),
                        usage.get("thinking_tokens", 0),
                        usage.get("active_tokens", 0),
                        usage.get("total_tokens", 0),
                        usage.get("estimated_cost_usd", 0.0),
                        conv_id
                    ))
            else:
                cursor.execute("""
                    UPDATE usage_records
                    SET input_tokens = CAST(input_tokens / 10 AS INTEGER),
                        output_tokens = CAST(output_tokens / 10 AS INTEGER),
                        cache_tokens = CAST(cache_tokens / 10 AS INTEGER),
                        thinking_tokens = CAST(thinking_tokens / 10 AS INTEGER),
                        active_tokens = CAST(active_tokens / 10 AS INTEGER),
                        total_tokens = CAST(total_tokens / 10 AS INTEGER),
                        estimated_cost_usd = estimated_cost_usd / 10.0
                    WHERE conversation_id = ?
                """, (conv_id,))
        conn.commit()
    except Exception as e:
        print(f"Error normalizing database {db_path}: {e}")
    finally:
        conn.close()


def save_qmd_metadata(record_data: dict[str, Any]) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO qmd_metadata (
                    point_id, project_id, module, feature_id, file_path, section_heading, updated_at, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record_data.get("point_id"),
                record_data.get("project_id"),
                record_data.get("module"),
                record_data.get("feature_id"),
                record_data.get("file_path"),
                record_data.get("section_heading"),
                record_data.get("updated_at") or datetime.now().astimezone().isoformat(),
                record_data.get("content_hash", "")
            ))
            conn.commit()
        finally:
            conn.close()


def get_qmd_metadata(filters: dict[str, Any]) -> list[dict[str, Any]]:
    conn = sqlite3.connect(PROJECT_DB)
    try:
        cursor = conn.cursor()
        query = "SELECT point_id, project_id, module, feature_id, file_path, section_heading, updated_at, content_hash FROM qmd_metadata WHERE 1=1"
        params: list[Any] = []
        for k, v in filters.items():
            query += f" AND {k} = ?"
            params.append(v)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        results: list[dict[str, Any]] = []
        for r in rows:
            results.append({
                "point_id": r[0],
                "project_id": r[1],
                "module": r[2],
                "feature_id": r[3],
                "file_path": r[4],
                "section_heading": r[5],
                "updated_at": r[6],
                "content_hash": r[7]
            })
        return results
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return []
        raise
    finally:
        conn.close()


def clear_qmd_metadata(project_id: str | None = None) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        if not os.path.exists(db_path):
            continue
        conn = sqlite3.connect(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()
            if project_id:
                cursor.execute("DELETE FROM qmd_metadata WHERE project_id = ?", (project_id,))
            else:
                cursor.execute("DELETE FROM qmd_metadata")
            conn.commit()
        finally:
            conn.close()


def save_usage_to_dbs(
    conversation_id: str = "",
    project_id: str = "",
    skill: str = "",
    command: str = "",
    usage: dict[str, Any] | None = None,
    *args: Any,
    **kwargs: Any,
) -> None:
    if not conversation_id or not usage:
        return
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
        datetime.now().astimezone().isoformat(),
    )
    for db_path in [get_project_db_path(), get_global_db_path()]:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            conn = connect_db(db_path)
            try:
                init_db_schema(conn)
                cursor = conn.cursor()
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
        except Exception:
            pass


def get_workflow_summary(
    conversation_id: str = "",
    provider: str = "estimate",
    model: str = "auto",
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    fallback = {
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
        "updated_at": datetime.now().astimezone().isoformat(),
    }
    db_path = get_project_db_path()
    if not conversation_id or not os.path.exists(db_path):
        return fallback
    try:
        conn = connect_db(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT input_tokens, output_tokens, cache_tokens, thinking_tokens, active_tokens, total_tokens,
                       estimated_cost_usd, provider, model, accuracy, timestamp
                FROM usage_records WHERE conversation_id = ?
            """, (conversation_id,))
            row = cursor.fetchone()
            if row:
                active_tokens = row[4] or 0
                return {
                    "provider": row[7] or provider,
                    "model": row[8] or model,
                    "input_tokens": row[0] or 0,
                    "output_tokens": row[1] or 0,
                    "cache_tokens": row[2] or 0,
                    "thinking_tokens": row[3] or 0,
                    "active_tokens": active_tokens,
                    "total_tokens": row[5] or 0,
                    "limit_tokens": 2000000,
                    "percentage": round((active_tokens / 2000000) * 100, 2),
                    "estimated_cost_usd": row[6] or 0.0,
                    "accuracy": row[9] or "estimated",
                    "updated_at": row[10] or datetime.now().astimezone().isoformat(),
                }
        finally:
            conn.close()
    except Exception:
        pass
    return fallback


def get_project_summary(
    project_id: str | None = None,
    *args: Any,
    **kwargs: Any,
) -> dict[str, Any]:
    fallback = {
        "project_id": project_id or "AIWF",
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "updated_at": datetime.now().astimezone().isoformat(),
    }
    db_path = get_project_db_path()
    if not os.path.exists(db_path):
        return fallback
    try:
        conn = connect_db(db_path)
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
                    "project_id": project_id or "AIWF",
                    "input_tokens": row[0] or 0,
                    "output_tokens": row[1] or 0,
                    "cache_tokens": row[2] or 0,
                    "thinking_tokens": row[3] or 0,
                    "total_tokens": row[4] or 0,
                    "estimated_cost_usd": round(row[5] or 0.0, 4),
                    "updated_at": datetime.now().astimezone().isoformat(),
                }
        finally:
            conn.close()
    except Exception:
        pass
    return fallback


__all__ = [
    "get_global_summary",
    "get_project_summary",
    "get_workflow_summary",
    "save_usage_to_dbs",
    "normalize_database_records",
    "save_qmd_metadata",
    "get_qmd_metadata",
    "clear_qmd_metadata",
]
