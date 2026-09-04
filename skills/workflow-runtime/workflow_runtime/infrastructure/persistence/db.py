"""Backward-compatible re-exports for persistence/db module."""
from __future__ import annotations

from .db_connections import (_custom_sqlite3_connect,  # pyright: ignore[reportPrivateUsage]
                             connect_db, get_global_db_path,
                             get_project_db_path, PROJECT_DB)
from .db_records import (_save_record, batch_insert_provider_requests,
                         clear_qmd_metadata, get_global_summary,
                         get_insight_snapshots, get_project_summary,
                         get_provider_request_detail, get_provider_requests,
                         get_qmd_metadata, get_recommendations,
                         get_timeline_events, get_token_diff,
                         get_workflow_summary, normalize_database_records,
                         save_insight_snapshot, save_provider_request,
                         save_qmd_metadata, save_recommendations,
                         save_timeline_event, save_token_diff,
                         save_usage_to_dbs, update_recommendation_status)
from .db_schema import init_db_schema

__all__ = [
    "_custom_sqlite3_connect",
    "get_project_db_path",
    "connect_db",
    "get_global_db_path",
    "PROJECT_DB",
    "init_db_schema",
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
    "save_timeline_event",
    "get_timeline_events",
    "save_usage_to_dbs",
    "get_workflow_summary",
    "get_project_summary",
    "get_global_summary",
    "normalize_database_records",
    "save_qmd_metadata",
    "get_qmd_metadata",
    "clear_qmd_metadata",
]
