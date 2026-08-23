# db.py
from __future__ import annotations

import sqlite3

_orig_sqlite3_connect = sqlite3.connect
_schemas_initialized: set[str] = set()


def init_db_schema(conn: sqlite3.Connection) -> None:
    db_name = str(getattr(conn, "_db_name_cache", "") or "")
    if not db_name:
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA database_list")
            row = cursor.fetchone()
            db_name = str(row[2]) if row and len(row) > 2 else "default"
            setattr(conn, "_db_name_cache", db_name)
        except Exception:
            db_name = "default"

    is_mem = not db_name or db_name == "default" or db_name == ":memory:"
    if not is_mem and db_name in _schemas_initialized:
        return

    if not is_mem:
        _schemas_initialized.add(db_name)
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

    # Create provider_requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS provider_requests (
            request_id TEXT PRIMARY KEY,
            workflow_id TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            project_id TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            command_name TEXT NOT NULL,
            model TEXT NOT NULL,
            provider TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            duration REAL NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cache_tokens INTEGER NOT NULL,
            thinking_tokens INTEGER NOT NULL,
            total_tokens INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            tool_call_count INTEGER NOT NULL,
            workspace_read_count INTEGER NOT NULL,
            memory_hit_count INTEGER NOT NULL,
            rag_hit_count INTEGER NOT NULL,
            context_usage_percentage REAL NOT NULL,
            context_limit_tokens INTEGER NOT NULL,
            context_breakdown_json TEXT,
            status TEXT NOT NULL,
            error_summary TEXT
        )
    """)

    # Indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_project_id ON provider_requests (project_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_workflow_id ON provider_requests (workflow_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_conversation_id ON provider_requests (conversation_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_created_at ON provider_requests (timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_requests_total_tokens ON provider_requests (total_tokens)")
    # Create token_diffs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_diffs (
            request_id TEXT PRIMARY KEY,
            prev_request_id TEXT,
            conversation_id TEXT NOT NULL,
            net_change_tokens INTEGER NOT NULL,
            percentage_change REAL NOT NULL,
            added_tokens INTEGER NOT NULL,
            removed_tokens INTEGER NOT NULL,
            diff_breakdown_json TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY(request_id) REFERENCES provider_requests(request_id)
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_diffs_conversation_id ON token_diffs(conversation_id)")

    # Create insight_snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insight_snapshots (
            timestamp TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            efficiency_score INTEGER NOT NULL,
            avg_tokens INTEGER NOT NULL,
            avg_cost REAL NOT NULL,
            growth_trend TEXT NOT NULL,
            insight_data_json TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_insights_conversation_id ON insight_snapshots(conversation_id)")

    # Create recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            token_savings INTEGER NOT NULL,
            cost_savings REAL NOT NULL,
            priority TEXT NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_recs_conversation_id ON recommendations(conversation_id)")

    # Create timeline_events table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS timeline_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            checkpoint INTEGER NOT NULL,
            skill TEXT NOT NULL,
            request_id TEXT,
            active_context INTEGER NOT NULL,
            context_delta INTEGER NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            cost REAL NOT NULL,
            duration REAL NOT NULL,
            details_json TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_conversation_id ON timeline_events(conversation_id)")

    # Prune duplicate request events from timeline
    cursor.execute("""
        DELETE FROM timeline_events
        WHERE request_id IS NOT NULL AND id NOT IN (
            SELECT MIN(id) FROM timeline_events
            WHERE request_id IS NOT NULL
            GROUP BY request_id
        )
    """)

    # Create budget_policies table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_policies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider TEXT NOT NULL UNIQUE,
            model TEXT NOT NULL,
            soft_warning_pct REAL NOT NULL DEFAULT 50.0,
            high_usage_pct REAL NOT NULL DEFAULT 70.0,
            critical_usage_pct REAL NOT NULL DEFAULT 85.0,
            emergency_pct REAL NOT NULL DEFAULT 95.0
        )
    """)

    # Create budget_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budget_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            predicted_tokens INTEGER NOT NULL,
            policy_triggered TEXT NOT NULL,
            strategy_applied TEXT NOT NULL,
            tokens_saved INTEGER NOT NULL,
            cost_saved REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # Create cache_metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cache_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_path TEXT NOT NULL UNIQUE,
            source_hash TEXT NOT NULL,
            summary_content TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Create context_bundles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS context_bundles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            original_tokens INTEGER NOT NULL,
            rebuilt_tokens INTEGER NOT NULL,
            tokens_saved INTEGER NOT NULL,
            included_sources TEXT NOT NULL,
            skipped_sources TEXT NOT NULL
        )
    """)

    # Create optimization_feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS optimization_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            savings_usd REAL NOT NULL
        )
    """)

    # Create benchmark_reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            original_input_tokens INTEGER NOT NULL,
            optimized_input_tokens INTEGER NOT NULL,
            original_cost REAL NOT NULL,
            optimized_cost REAL NOT NULL
        )
    """)

    # Create policy_configurations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS policy_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            policy_name TEXT NOT NULL UNIQUE,
            context_rebuild_enabled INTEGER NOT NULL DEFAULT 1,
            cache_enabled INTEGER NOT NULL DEFAULT 1,
            compression_pct REAL NOT NULL DEFAULT 85.0
        )
    """)

    # Create qmd_metadata table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qmd_metadata (
            point_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            module TEXT,
            feature_id TEXT,
            file_path TEXT NOT NULL,
            section_heading TEXT,
            updated_at TEXT NOT NULL,
            content_hash TEXT NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_qmd_project_module ON qmd_metadata (project_id, module)")
    conn.commit()

    # ------------------------------------------------------------------ #
    # FEAT-048: Provider-Centric Runtime & Usage Engine — additive migrations
    # ------------------------------------------------------------------ #

    # transcript_cursors: incremental reader byte-position tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcript_cursors (
            file_path   TEXT PRIMARY KEY,
            byte_pos    INTEGER NOT NULL DEFAULT 0,
            file_hash   TEXT NOT NULL DEFAULT '',
            updated_at  TEXT NOT NULL
        )
    """)

    # runtime_events: durable event journal (Phase 1 — SQLite only per ADR-005)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runtime_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id        TEXT NOT NULL UNIQUE,
            timestamp       TEXT NOT NULL,
            conversation_id TEXT NOT NULL,
            provider        TEXT NOT NULL,
            event_type      TEXT NOT NULL,
            event_data_json TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_runtime_events_conv "
        "ON runtime_events (conversation_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_runtime_events_type "
        "ON runtime_events (event_type)"
    )

    # connector_diagnostics: per-provider status snapshots
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connector_diagnostics (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           TEXT NOT NULL,
            provider            TEXT NOT NULL,
            status              TEXT NOT NULL,
            detected_path       TEXT,
            error_message       TEXT,
            accuracy_confidence TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_connector_diag_provider "
        "ON connector_diagnostics (provider)"
    )

    # Additive columns on provider_requests (safe: try/except OperationalError)
    try:
        cursor.execute(
            "ALTER TABLE provider_requests ADD COLUMN accuracy_source TEXT DEFAULT 'estimated'"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists — normal on subsequent runs

    try:
        cursor.execute(
            "ALTER TABLE provider_requests ADD COLUMN raw_payload TEXT"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass  # column already exists — normal on subsequent runs

    # ------------------------------------------------------------------ #
    # FEAT-049: Transcript-First Accounting System — schema migrations
    # ------------------------------------------------------------------ #

    # request_fingerprints: canonical request identity for deduplication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_fingerprints (
            fingerprint     TEXT PRIMARY KEY,
            provider        TEXT NOT NULL,
            conv_id         TEXT NOT NULL,
            request_id      TEXT NOT NULL,
            model           TEXT NOT NULL,
            timestamp       TEXT NOT NULL,
            duplicate_count INTEGER NOT NULL DEFAULT 0,
            first_seen      TEXT NOT NULL,
            last_seen       TEXT NOT NULL
        )
    """)
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_fingerprints_hash "
        "ON request_fingerprints (fingerprint)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_fingerprints_conv "
        "ON request_fingerprints (conv_id)"
    )

    # pricing_versions: versioned pricing rates per model
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pricing_versions (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            provider             TEXT NOT NULL,
            model                TEXT NOT NULL,
            version              TEXT NOT NULL,
            effective_date       TEXT NOT NULL,
            input_per_mtok       REAL NOT NULL DEFAULT 0.0,
            output_per_mtok      REAL NOT NULL DEFAULT 0.0,
            cache_read_per_mtok  REAL NOT NULL DEFAULT 0.0,
            cache_write_per_mtok REAL NOT NULL DEFAULT 0.0,
            thinking_per_mtok    REAL NOT NULL DEFAULT 0.0,
            tool_per_mtok        REAL NOT NULL DEFAULT 0.0,
            created_at           TEXT NOT NULL,
            UNIQUE (provider, model, version)
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_pricing_versions_effective "
        "ON pricing_versions (provider, model, effective_date DESC)"
    )

    # reconciliation_reports: logs of sync cycles and metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reconciliation_reports (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp               TEXT NOT NULL,
            requests_discovered     INTEGER NOT NULL DEFAULT 0,
            requests_parsed         INTEGER NOT NULL DEFAULT 0,
            duplicates_ignored      INTEGER NOT NULL DEFAULT 0,
            corrupted_transcripts   INTEGER NOT NULL DEFAULT 0,
            missing_usage_metadata  INTEGER NOT NULL DEFAULT 0,
            reconstructed_usage     INTEGER NOT NULL DEFAULT 0,
            estimated_usage         INTEGER NOT NULL DEFAULT 0,
            confidence_score        REAL NOT NULL DEFAULT 0.0,
            duration_ms             INTEGER NOT NULL DEFAULT 0
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reconciliation_timestamp "
        "ON reconciliation_reports (timestamp DESC)"
    )

    # Additive columns on provider_requests (safe: try/except OperationalError)
    try:
        cursor.execute(
            "ALTER TABLE provider_requests ADD COLUMN fingerprint TEXT"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE provider_requests ADD COLUMN pricing_version TEXT DEFAULT ''"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE provider_requests ADD COLUMN tool_tokens INTEGER DEFAULT 0"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE provider_requests ADD COLUMN transcript_offset INTEGER DEFAULT -1"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    conn.commit()
