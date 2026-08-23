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


def get_provider_requests(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if not os.path.exists(PROJECT_DB):
        return []
    conn = connect_db(PROJECT_DB)
    try:
        cursor = conn.cursor()
        query = "SELECT request_id, conversation_id, skill_name, command_name, model, provider, timestamp, duration, input_tokens, output_tokens, total_tokens, cost_usd, status FROM provider_requests WHERE 1=1"
        params: list[Any] = []
        if filters:
            for k, v in filters.items():
                query += f" AND {k} = ?"
                params.append(v)
        query += " ORDER BY timestamp DESC LIMIT 100"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [
            {
                "request_id": r[0], "conversation_id": r[1], "skill_name": r[2],
                "command_name": r[3], "model": r[4], "provider": r[5],
                "timestamp": r[6], "duration": r[7], "input_tokens": r[8],
                "output_tokens": r[9], "total_tokens": r[10], "cost_usd": r[11],
                "status": r[12]
            }
            for r in rows
        ]
    except Exception:
        return []
    finally:
        conn.close()


def get_provider_request_detail(request_id: str) -> dict[str, Any] | None:
    reqs = get_provider_requests({"request_id": request_id})
    return reqs[0] if reqs else None


def save_token_diff(diff_data: dict[str, Any]) -> None:
    pass


def get_token_diff(conversation_id: str) -> dict[str, Any] | None:
    return None


def save_insight_snapshot(snapshot: dict[str, Any]) -> None:
    pass


def get_insight_snapshots(conversation_id: str) -> list[dict[str, Any]]:
    return []


def save_recommendations(recs: list[dict[str, Any]]) -> None:
    pass


def get_recommendations(conversation_id: str) -> list[dict[str, Any]]:
    return []


def update_recommendation_status(rec_id: str, status: str) -> None:
    pass


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
