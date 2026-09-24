"""
workflow_runtime/infrastructure/persistence/provider_usage_records.py

Database records adapter for provider requests, token usage, and cost tracking.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any

from workflow_runtime.infrastructure.persistence.db_connections import (
    PROJECT_DB, connect_db, get_global_db_path)
from workflow_runtime.infrastructure.persistence.db_schema import (
    init_db_schema)


def _save_record(db_path: str, record: tuple[Any, ...]) -> None:
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


def save_provider_request(request_data: dict[str, Any]) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = connect_db(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()

            cb_json = request_data.get("context_breakdown_json")
            if isinstance(cb_json, (dict, list)):
                cb_json = json.dumps(cb_json)

            record = (
                request_data.get("request_id"),
                request_data.get("workflow_id"),
                request_data.get("conversation_id"),
                request_data.get("project_id"),
                request_data.get("skill_name"),
                request_data.get("command_name"),
                request_data.get("model"),
                request_data.get("provider"),
                request_data.get("timestamp") or datetime.now().astimezone().isoformat(),
                request_data.get("duration", 0.0),
                request_data.get("input_tokens", 0),
                request_data.get("output_tokens", 0),
                request_data.get("cache_tokens", 0),
                request_data.get("thinking_tokens", 0),
                request_data.get("total_tokens", 0),
                request_data.get("cost_usd", 0.0),
                request_data.get("tool_call_count", 0),
                request_data.get("workspace_read_count", 0),
                request_data.get("memory_hit_count", 0),
                request_data.get("rag_hit_count", 0),
                request_data.get("context_usage_percentage", 0.0),
                request_data.get("context_limit_tokens", 2000000),
                cb_json,
                request_data.get("status", "success"),
                request_data.get("error_summary"),
                request_data.get("fingerprint"),
                request_data.get("pricing_version", ""),
                request_data.get("tool_tokens", 0),
                request_data.get("transcript_offset", -1)
            )

            cursor.execute("""
                INSERT OR IGNORE INTO provider_requests (
                    request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
                    model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
                    thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
                    memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens,
                    context_breakdown_json, status, error_summary, fingerprint, pricing_version,
                    tool_tokens, transcript_offset
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()
        finally:
            conn.close()


def batch_insert_provider_requests(records: list[dict[str, Any]], batch_size: int = 1000) -> int:
    if not records:
        return 0

    inserted_count = 0
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = connect_db(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                tuples_to_insert = []

                for request_data in batch:
                    cb_json = request_data.get("context_breakdown_json")
                    if isinstance(cb_json, (dict, list)):
                        cb_json = json.dumps(cb_json)

                    tuples_to_insert.append((
                        request_data.get("request_id"),
                        request_data.get("workflow_id"),
                        request_data.get("conversation_id"),
                        request_data.get("project_id"),
                        request_data.get("skill_name"),
                        request_data.get("command_name"),
                        request_data.get("model"),
                        request_data.get("provider"),
                        request_data.get("timestamp") or datetime.now().astimezone().isoformat(),
                        request_data.get("duration", 0.0),
                        request_data.get("input_tokens", 0),
                        request_data.get("output_tokens", 0),
                        request_data.get("cache_tokens", 0),
                        request_data.get("thinking_tokens", 0),
                        request_data.get("total_tokens", 0),
                        request_data.get("cost_usd", 0.0),
                        request_data.get("tool_call_count", 0),
                        request_data.get("workspace_read_count", 0),
                        request_data.get("memory_hit_count", 0),
                        request_data.get("rag_hit_count", 0),
                        request_data.get("context_usage_percentage", 0.0),
                        request_data.get("context_limit_tokens", 2000000),
                        cb_json,
                        request_data.get("status", "success"),
                        request_data.get("error_summary"),
                        request_data.get("fingerprint"),
                        request_data.get("pricing_version", ""),
                        request_data.get("tool_tokens", 0),
                        request_data.get("transcript_offset", -1)
                    ))

                cursor.executemany("""
                    INSERT OR IGNORE INTO provider_requests (
                        request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
                        model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
                        thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
                        memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens,
                        context_breakdown_json, status, error_summary, fingerprint, pricing_version,
                        tool_tokens, transcript_offset
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, tuples_to_insert)
                conn.commit()
                inserted_count += cursor.rowcount
        finally:
            conn.close()

    return inserted_count


_REQUEST_COLUMNS = (
    "request_id", "workflow_id", "conversation_id", "project_id", "skill_name", "command_name",
    "model", "provider", "timestamp", "duration", "input_tokens", "output_tokens", "cache_tokens",
    "thinking_tokens", "total_tokens", "cost_usd", "tool_call_count", "workspace_read_count",
    "memory_hit_count", "rag_hit_count", "context_usage_percentage", "context_limit_tokens",
    "context_breakdown_json", "status", "error_summary", "fingerprint", "pricing_version",
    "tool_tokens", "transcript_offset",
)
_ALLOWED_SORTS = {"timestamp", "cost_usd", "total_tokens", "input_tokens", "duration", "context_usage_percentage"}


def get_provider_requests(
    filters: dict[str, Any] | None = None,
    sort_by: str = "timestamp",
    desc: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    if not os.path.exists(PROJECT_DB):
        return []
    filters = filters or {}
    conn = connect_db(PROJECT_DB)
    try:
        cursor = conn.cursor()
        query = f"SELECT {', '.join(_REQUEST_COLUMNS)} FROM provider_requests"
        where_clauses: list[str] = []
        params: list[Any] = []
        for key, val in filters.items():
            if key in ("start_time", "end_time") or val is None:
                continue
            if key not in _REQUEST_COLUMNS:
                raise ValueError(f"Unsupported provider_requests filter: {key}")
            where_clauses.append(f"{key} = ?")
            params.append(val)
        if filters.get("start_time") is not None:
            where_clauses.append("timestamp >= ?")
            params.append(filters["start_time"])
        if filters.get("end_time") is not None:
            where_clauses.append("timestamp <= ?")
            params.append(filters["end_time"])
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        order_col = sort_by if sort_by in _ALLOWED_SORTS else "timestamp"
        query += f" ORDER BY {order_col} {'DESC' if desc else 'ASC'}"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        cursor.execute(query, params)
        return [dict(zip(_REQUEST_COLUMNS, r)) for r in cursor.fetchall()]
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return []
        raise
    finally:
        conn.close()


def get_provider_request_detail(request_id: str) -> dict[str, Any] | None:
    reqs = get_provider_requests({"request_id": request_id}, limit=1)
    return reqs[0] if reqs else None


def save_token_diff(diff_data: dict[str, Any]) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = connect_db(db_path)
        try:
            init_db_schema(conn)
            categories = diff_data.get("categories")
            if isinstance(categories, (dict, list)):
                categories = json.dumps(categories)
            conn.execute("""
                INSERT OR IGNORE INTO token_diffs (
                    request_id, prev_request_id, conversation_id, net_change_tokens,
                    percentage_change, added_tokens, removed_tokens, diff_breakdown_json, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                diff_data.get("request_id"),
                diff_data.get("prev_request_id"),
                diff_data.get("conversation_id"),
                diff_data.get("net_change_tokens", 0),
                diff_data.get("percentage_change", 0.0),
                diff_data.get("added_tokens", 0),
                diff_data.get("removed_tokens", 0),
                categories,
                diff_data.get("timestamp") or datetime.now().astimezone().isoformat(),
            ))
            conn.commit()
        finally:
            conn.close()


def get_token_diff(request_id: str) -> dict[str, Any] | None:
    if not os.path.exists(PROJECT_DB):
        return None
    conn = connect_db(PROJECT_DB)
    try:
        r = conn.execute("""
            SELECT request_id, prev_request_id, conversation_id, net_change_tokens,
                   percentage_change, added_tokens, removed_tokens, diff_breakdown_json, timestamp
            FROM token_diffs
            WHERE request_id = ?
        """, (request_id,)).fetchone()
        if not r:
            return None
        try:
            categories = json.loads(r[7])
        except (TypeError, ValueError):
            categories = {}
        return {
            "request_id": r[0],
            "prev_request_id": r[1],
            "conversation_id": r[2],
            "net_change_tokens": r[3],
            "percentage_change": r[4],
            "added_tokens": r[5],
            "removed_tokens": r[6],
            "categories": categories,
            "timestamp": r[8],
        }
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return None
        raise
    finally:
        conn.close()


def save_insight_snapshot(snapshot: dict[str, Any]) -> None:
    data = snapshot.get("insight_data")
    data_json = json.dumps(data) if isinstance(data, (dict, list)) else (data or "{}")
    record = (
        snapshot.get("timestamp") or datetime.now().astimezone().isoformat(),
        snapshot.get("conversation_id"),
        snapshot.get("efficiency_score", 100),
        snapshot.get("avg_tokens", 0),
        snapshot.get("avg_cost", 0.0),
        snapshot.get("growth_trend", "stable"),
        data_json,
    )
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = connect_db(db_path)
        try:
            init_db_schema(conn)
            conn.execute("""
                INSERT OR REPLACE INTO insight_snapshots (
                    timestamp, conversation_id, efficiency_score, avg_tokens,
                    avg_cost, growth_trend, insight_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()
        finally:
            conn.close()


def get_insight_snapshots(conversation_id: str) -> list[dict[str, Any]]:
    if not os.path.exists(PROJECT_DB):
        return []
    conn = connect_db(PROJECT_DB)
    try:
        rows = conn.execute("""
            SELECT timestamp, conversation_id, efficiency_score, avg_tokens,
                   avg_cost, growth_trend, insight_data_json
            FROM insight_snapshots WHERE conversation_id = ? ORDER BY timestamp DESC
        """, (conversation_id,)).fetchall()
        results: list[dict[str, Any]] = []
        for r in rows:
            try:
                data = json.loads(r[6])
            except Exception:
                data = {}
            results.append({
                "timestamp": r[0], "conversation_id": r[1], "efficiency_score": r[2],
                "avg_tokens": r[3], "avg_cost": r[4], "growth_trend": r[5], "insight_data": data,
            })
        return results
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return []
        raise
    finally:
        conn.close()


_RECOMMENDATION_COLUMNS = (
    "id", "conversation_id", "type", "description", "token_savings",
    "cost_savings", "priority", "confidence", "status", "timestamp",
)


def save_recommendations(recs: list[dict[str, Any]]) -> None:
    records = [
        (
            r.get("id"), r.get("conversation_id"), r.get("type"), r.get("description"),
            r.get("token_savings", 0), r.get("cost_savings", 0.0), r.get("priority", "Medium"),
            r.get("confidence", 0.8), r.get("status", "pending"),
            r.get("timestamp") or datetime.now().astimezone().isoformat(),
        )
        for r in recs
    ]
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = connect_db(db_path)
        try:
            init_db_schema(conn)
            conn.executemany(f"""
                INSERT OR IGNORE INTO recommendations ({', '.join(_RECOMMENDATION_COLUMNS)})
                VALUES ({', '.join('?' * len(_RECOMMENDATION_COLUMNS))})
            """, records)
            conn.commit()
        finally:
            conn.close()


def get_recommendations(conversation_id: str) -> list[dict[str, Any]]:
    if not os.path.exists(PROJECT_DB):
        return []
    conn = connect_db(PROJECT_DB)
    try:
        rows = conn.execute(
            f"SELECT {', '.join(_RECOMMENDATION_COLUMNS)} FROM recommendations"
            " WHERE conversation_id = ? ORDER BY timestamp DESC",
            (conversation_id,),
        ).fetchall()
        return [dict(zip(_RECOMMENDATION_COLUMNS, r)) for r in rows]
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return []
        raise
    finally:
        conn.close()


def update_recommendation_status(rec_id: str, status: str) -> bool:
    success = False
    for db_path in [PROJECT_DB, get_global_db_path()]:
        if not os.path.exists(db_path):
            continue
        conn = connect_db(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.execute("UPDATE recommendations SET status = ? WHERE id = ?", (status, rec_id))
            success = success or cursor.rowcount > 0
            conn.commit()
        finally:
            conn.close()
    return success


__all__ = [
    "_save_record",
    "save_provider_request",
    "batch_insert_provider_requests",
    "get_provider_requests",
    "get_provider_request_detail",
    "save_token_diff",
    "get_token_diff",
    "save_insight_snapshot",
    "get_insight_snapshots",
    "save_recommendations",
    "get_recommendations",
    "update_recommendation_status",
]
