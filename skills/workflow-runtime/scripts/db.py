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

import json

def init_db_schema(conn: sqlite3.Connection) -> None:
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
    conn.commit()

def _save_record(db_path: str, record: tuple) -> None:
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
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

def save_provider_request(request_data: dict) -> None:
    # Ensure parent dir exists
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
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
                request_data.get("error_summary")
            )
            
            cursor.execute("""
                INSERT OR IGNORE INTO provider_requests (
                    request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
                    model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
                    thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
                    memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens,
                    context_breakdown_json, status, error_summary
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()
        finally:
            conn.close()

def get_provider_requests(filters: dict, sort_by: str = "timestamp", desc: bool = True, limit: int = None) -> list[dict]:
    if not os.path.exists(PROJECT_DB):
        return []
    
    conn = sqlite3.connect(PROJECT_DB)
    try:
        init_db_schema(conn)
        cursor = conn.cursor()
        
        query = """
            SELECT request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
                   model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
                   thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
                   memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens,
                   context_breakdown_json, status, error_summary
            FROM provider_requests
        """
        
        where_clauses = []
        params = []
        for key, val in filters.items():
            if key in ["start_time", "end_time"]:
                continue
            if val is not None:
                where_clauses.append(f"{key} = ?")
                params.append(val)
                
        if "start_time" in filters and filters["start_time"] is not None:
            where_clauses.append("timestamp >= ?")
            params.append(filters["start_time"])
            
        if "end_time" in filters and filters["end_time"] is not None:
            where_clauses.append("timestamp <= ?")
            params.append(filters["end_time"])
                 
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        allowed_sorts = {
            "timestamp": "timestamp",
            "cost_usd": "cost_usd",
            "total_tokens": "total_tokens",
            "input_tokens": "input_tokens",
            "duration": "duration",
            "context_usage_percentage": "context_usage_percentage"
        }
        order_col = allowed_sorts.get(sort_by, "timestamp")
        direction = "DESC" if desc else "ASC"
        query += f" ORDER BY {order_col} {direction}"
        
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "request_id": r[0],
                "workflow_id": r[1],
                "conversation_id": r[2],
                "project_id": r[3],
                "skill_name": r[4],
                "command_name": r[5],
                "model": r[6],
                "provider": r[7],
                "timestamp": r[8],
                "duration": r[9],
                "input_tokens": r[10],
                "output_tokens": r[11],
                "cache_tokens": r[12],
                "thinking_tokens": r[13],
                "total_tokens": r[14],
                "cost_usd": r[15],
                "tool_call_count": r[16],
                "workspace_read_count": r[17],
                "memory_hit_count": r[18],
                "rag_hit_count": r[19],
                "context_usage_percentage": r[20],
                "context_limit_tokens": r[21],
                "context_breakdown_json": r[22],
                "status": r[23],
                "error_summary": r[24]
            })
        return results
    finally:
        conn.close()

def get_provider_request_detail(request_id: str) -> dict:
    results = get_provider_requests({"request_id": request_id}, limit=1)
    return results[0] if results else None

def save_token_diff(diff_data: dict) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()
            
            db_json = diff_data.get("categories")
            if isinstance(db_json, (dict, list)):
                db_json = json.dumps(db_json)
                
            record = (
                diff_data.get("request_id"),
                diff_data.get("prev_request_id"),
                diff_data.get("conversation_id"),
                diff_data.get("net_change_tokens", 0),
                diff_data.get("percentage_change", 0.0),
                diff_data.get("added_tokens", 0),
                diff_data.get("removed_tokens", 0),
                db_json,
                diff_data.get("timestamp") or datetime.now().astimezone().isoformat()
            )
            
            cursor.execute("""
                INSERT OR IGNORE INTO token_diffs (
                    request_id, prev_request_id, conversation_id, net_change_tokens,
                    percentage_change, added_tokens, removed_tokens, diff_breakdown_json, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()
        finally:
            conn.close()

def get_token_diff(request_id: str) -> dict:
    if not os.path.exists(PROJECT_DB):
        return None
        
    conn = sqlite3.connect(PROJECT_DB)
    try:
        init_db_schema(conn)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT request_id, prev_request_id, conversation_id, net_change_tokens,
                   percentage_change, added_tokens, removed_tokens, diff_breakdown_json, timestamp
            FROM token_diffs
            WHERE request_id = ?
        """, (request_id,))
        r = cursor.fetchone()
        if r:
            try:
                cats = json.loads(r[7])
            except Exception:
                cats = {}
            return {
                "request_id": r[0],
                "prev_request_id": r[1],
                "conversation_id": r[2],
                "net_change_tokens": r[3],
                "percentage_change": r[4],
                "added_tokens": r[5],
                "removed_tokens": r[6],
                "categories": cats,
                "timestamp": r[8]
            }
        return None
    finally:
        conn.close()

def save_insight_snapshot(snapshot: dict) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()
            
            data_json = snapshot.get("insight_data")
            if isinstance(data_json, (dict, list)):
                data_json = json.dumps(data_json)
                
            record = (
                snapshot.get("timestamp") or datetime.now().astimezone().isoformat(),
                snapshot.get("conversation_id"),
                snapshot.get("efficiency_score", 100),
                snapshot.get("avg_tokens", 0),
                snapshot.get("avg_cost", 0.0),
                snapshot.get("growth_trend", "stable"),
                data_json or "{}"
            )
            
            cursor.execute("""
                INSERT OR REPLACE INTO insight_snapshots (
                    timestamp, conversation_id, efficiency_score, avg_tokens,
                    avg_cost, growth_trend, insight_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()
        finally:
            conn.close()

def get_insight_snapshots(conversation_id: str) -> list[dict]:
    if not os.path.exists(PROJECT_DB):
        return []
    conn = sqlite3.connect(PROJECT_DB)
    try:
        init_db_schema(conn)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, conversation_id, efficiency_score, avg_tokens,
                   avg_cost, growth_trend, insight_data_json
            FROM insight_snapshots
            WHERE conversation_id = ?
            ORDER BY timestamp DESC
        """, (conversation_id,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            try:
                data = json.loads(r[6])
            except Exception:
                data = {}
            results.append({
                "timestamp": r[0],
                "conversation_id": r[1],
                "efficiency_score": r[2],
                "avg_tokens": r[3],
                "avg_cost": r[4],
                "growth_trend": r[5],
                "insight_data": data
            })
        return results
    finally:
        conn.close()

def save_recommendations(recs: list[dict]) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()
            for r in recs:
                record = (
                    r.get("id"),
                    r.get("conversation_id"),
                    r.get("type"),
                    r.get("description"),
                    r.get("token_savings", 0),
                    r.get("cost_savings", 0.0),
                    r.get("priority", "Medium"),
                    r.get("confidence", 0.8),
                    r.get("status", "pending"),
                    r.get("timestamp") or datetime.now().astimezone().isoformat()
                )
                cursor.execute("""
                    INSERT OR IGNORE INTO recommendations (
                        id, conversation_id, type, description, token_savings,
                        cost_savings, priority, confidence, status, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, record)
            conn.commit()
        finally:
            conn.close()

def get_recommendations(conversation_id: str) -> list[dict]:
    if not os.path.exists(PROJECT_DB):
        return []
    conn = sqlite3.connect(PROJECT_DB)
    try:
        init_db_schema(conn)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, conversation_id, type, description, token_savings,
                   cost_savings, priority, confidence, status, timestamp
            FROM recommendations
            WHERE conversation_id = ?
            ORDER BY timestamp DESC
        """, (conversation_id,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "conversation_id": r[1],
                "type": r[2],
                "description": r[3],
                "token_savings": r[4],
                "cost_savings": r[5],
                "priority": r[6],
                "confidence": r[7],
                "status": r[8],
                "timestamp": r[9]
            })
        return results
    finally:
        conn.close()

def update_recommendation_status(rec_id: str, status: str) -> bool:
    success = False
    for db_path in [PROJECT_DB, get_global_db_path()]:
        if not os.path.exists(db_path):
            continue
        conn = sqlite3.connect(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE recommendations
                SET status = ?
                WHERE id = ?
            """, (status, rec_id))
            if cursor.rowcount > 0:
                success = True
            conn.commit()
        finally:
            conn.close()
    return success

def save_timeline_event(event: dict) -> None:
    for db_path in [PROJECT_DB, get_global_db_path()]:
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            init_db_schema(conn)
            cursor = conn.cursor()
            
            # Skip if request_id event already logged
            if event.get("request_id"):
                cursor.execute(
                    "SELECT 1 FROM timeline_events WHERE request_id = ? AND event_type = ?",
                    (event["request_id"], event.get("event_type", "Provider request"))
                )
                if cursor.fetchone():
                    continue
            
            details_json = event.get("details")
            if isinstance(details_json, (dict, list)):
                details_json = json.dumps(details_json)
                
            record = (
                event.get("timestamp") or datetime.now().astimezone().isoformat(),
                event.get("conversation_id"),
                event.get("event_type"),
                event.get("checkpoint", 1),
                event.get("skill") or "unknown",
                event.get("request_id"),
                event.get("active_context", 0),
                event.get("context_delta", 0),
                event.get("input_tokens", 0),
                event.get("output_tokens", 0),
                event.get("cost", 0.0),
                event.get("duration", 0.0),
                details_json or "{}"
            )
            
            cursor.execute("""
                INSERT INTO timeline_events (
                    timestamp, conversation_id, event_type, checkpoint, skill,
                    request_id, active_context, context_delta, input_tokens,
                    output_tokens, cost, duration, details_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, record)
            conn.commit()
        finally:
            conn.close()

def get_timeline_events(conversation_id: str) -> list[dict]:
    if not os.path.exists(PROJECT_DB):
        return []
    conn = sqlite3.connect(PROJECT_DB)
    try:
        init_db_schema(conn)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, conversation_id, event_type, checkpoint, skill,
                   request_id, active_context, context_delta, input_tokens,
                   output_tokens, cost, duration, details_json
            FROM timeline_events
            WHERE conversation_id = ?
            ORDER BY timestamp ASC
        """, (conversation_id,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            try:
                details = json.loads(r[13])
            except Exception:
                details = {}
            results.append({
                "id": r[0],
                "timestamp": r[1],
                "conversation_id": r[2],
                "event_type": r[3],
                "checkpoint": r[4],
                "skill": r[5],
                "request_id": r[6],
                "active_context": r[7],
                "context_delta": r[8],
                "input_tokens": r[9],
                "output_tokens": r[10],
                "cost": r[11],
                "duration": r[12],
                "details": details
            })
        return results
    finally:
        conn.close()

def save_usage_to_dbs(conversation_id: str, project_id: str, skill: str, command: str, usage: dict) -> None:
    if "accumulated_usage" in usage:
        # Structured payload
        new_total = usage["accumulated_usage"].get("total_tokens", 0)
        active_context_tokens = usage["active_context"].get("total_tokens", 0)
        input_tokens = usage["accumulated_usage"].get("input_tokens", 0)
        output_tokens = usage["accumulated_usage"].get("output_tokens", 0)
        cache_tokens = usage["accumulated_usage"].get("cache_tokens", 0)
        thinking_tokens = usage["accumulated_usage"].get("thinking_tokens", 0)
        estimated_cost_usd = usage["accumulated_usage"].get("estimated_cost_usd", 0.0)
        provider = usage.get("provider", "unknown")
        model = usage.get("model", "unknown")
        accuracy = usage.get("accuracy", "unknown")
    else:
        # Flat legacy payload
        new_total = usage.get("total_tokens", 0)
        active_context_tokens = usage.get("active_tokens", 0)
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        cache_tokens = usage.get("cache_tokens", 0)
        thinking_tokens = usage.get("thinking_tokens", 0)
        estimated_cost_usd = usage.get("estimated_cost_usd", 0.0)
        provider = usage.get("provider", "unknown")
        model = usage.get("model", "unknown")
        accuracy = usage.get("accuracy", "unknown")
        
    # Read existing total_tokens from Project DB if it exists
    existing_total = 0
    if os.path.exists(PROJECT_DB):
        conn = sqlite3.connect(PROJECT_DB)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'")
            if cursor.fetchone():
                cursor.execute("SELECT total_tokens FROM usage_records WHERE conversation_id = ?", (conversation_id,))
                row = cursor.fetchone()
                if row:
                    existing_total = row[0]
        except Exception:
            pass
        finally:
            conn.close()
            
    if command != "init" and new_total <= existing_total and existing_total > 0:
        # Keep existing record if new estimate is smaller or equal
        return

    record = (
        conversation_id,
        project_id,
        skill,
        command,
        input_tokens,
        output_tokens,
        cache_tokens,
        thinking_tokens,
        active_context_tokens,
        new_total,
        estimated_cost_usd,
        provider,
        model,
        accuracy,
        datetime.now().astimezone().isoformat()
    )
    
    # Save to Project DB
    _save_record(PROJECT_DB, record)
    
    # Save to Global DB
    global_db = get_global_db_path()
    _save_record(global_db, record)

def get_workflow_summary(conversation_id: str, provider: str, model: str) -> dict:
    fallback = {
        "provider": provider,
        "model": model,
        "active_context": {
            "total_tokens": 0,
            "limit_tokens": 2000000,
            "percentage": 0.0
        },
        "accumulated_usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_tokens": 0,
            "thinking_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
            "request_count": 0
        },
        "efficiency": {
            "cache_hit_ratio": 0.15,
            "input_to_output_ratio": 49.0
        },
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
    
    if not os.path.exists(PROJECT_DB):
        return fallback

    conn = None
    try:
        conn = sqlite3.connect(PROJECT_DB)
        cursor = conn.cursor()
        
        has_requests = False
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provider_requests'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM provider_requests WHERE conversation_id = ?", (conversation_id,))
            if cursor.fetchone()[0] > 0:
                has_requests = True
                
        if not has_requests:
            # Fall back to usage_records table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'")
            if cursor.fetchone():
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
                        "active_context": {
                            "total_tokens": active_tokens,
                            "limit_tokens": 2000000,
                            "percentage": round((active_tokens / 2000000) * 100, 2)
                        },
                        "accumulated_usage": {
                            "input_tokens": row[0] or 0,
                            "output_tokens": row[1] or 0,
                            "cache_tokens": row[2] or 0,
                            "thinking_tokens": row[3] or 0,
                            "total_tokens": row[5] or 0,
                            "estimated_cost_usd": row[6] or 0.0,
                            "request_count": 1
                        },
                        "efficiency": {
                            "cache_hit_ratio": round((row[2] or 0) / max(1, row[0] or 1), 2),
                            "input_to_output_ratio": round(((row[1] or 0) / max(1, row[0] or 1)) * 100, 2)
                        },
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
                        "updated_at": row[10] or datetime.now().astimezone().isoformat()
                    }
            return fallback
            
        cursor.execute("""
            SELECT COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens), SUM(thinking_tokens), SUM(cost_usd),
                   SUM(memory_hit_count), SUM(rag_hit_count)
            FROM provider_requests WHERE conversation_id = ?
        """, (conversation_id,))
        agg = cursor.fetchone()
        
        cursor.execute("""
            SELECT total_tokens, provider, model, timestamp FROM provider_requests
            WHERE conversation_id = ?
            ORDER BY timestamp DESC LIMIT 1
        """, (conversation_id,))
        latest = cursor.fetchone()

        if agg and agg[0] > 0:
            request_count = agg[0]
            input_tokens = agg[1] or 0
            output_tokens = agg[2] or 0
            cache_tokens = agg[3] or 0
            thinking_tokens = agg[4] or 0
            cost = round(agg[5] or 0.0, 6)
            memory_hits = agg[6] or 0
            rag_hits = agg[7] or 0
            
            active_tokens = latest[0] if latest else 0
            prov = latest[1] if latest else provider
            mdl = latest[2] if latest else model
            ts = latest[3] if latest else datetime.now().astimezone().isoformat()
            
            total_tokens = input_tokens + output_tokens
            cache_hit_ratio = round(cache_tokens / max(1, input_tokens), 2)
            io_ratio = round((output_tokens / max(1, input_tokens)) * 100, 2)
            memory_hit_ratio = min(1.0, round(memory_hits / max(1, request_count), 2))
            rag_hit_ratio = min(1.0, round(rag_hits / max(1, request_count), 2))
            
            return {
                "provider": prov,
                "model": mdl,
                "active_context": {
                    "total_tokens": active_tokens,
                    "limit_tokens": 2000000,
                    "percentage": round((active_tokens / 2000000) * 100, 2)
                },
                "accumulated_usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_tokens": cache_tokens,
                    "thinking_tokens": thinking_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": cost,
                    "request_count": request_count
                },
                "efficiency": {
                    "cache_hit_ratio": cache_hit_ratio,
                    "input_to_output_ratio": io_ratio,
                    "memory_hit_ratio": memory_hit_ratio,
                    "rag_hit_ratio": rag_hit_ratio
                },
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_tokens": cache_tokens,
                "thinking_tokens": thinking_tokens,
                "active_tokens": active_tokens,
                "total_tokens": total_tokens,
                "limit_tokens": 2000000,
                "percentage": round((active_tokens / 2000000) * 100, 2),
                "estimated_cost_usd": cost,
                "accuracy": "calculated",
                "updated_at": ts
            }
    except Exception as e:
        print(f"Error fetching workflow summary: {e}")
    finally:
        if conn:
            conn.close()
            
    return fallback

def get_project_summary(project_id: str) -> dict:
    fallback = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_tokens": 0,
        "thinking_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "updated_at": datetime.now().astimezone().isoformat()
    }
    if not os.path.exists(PROJECT_DB):
        return fallback

    conn = None
    try:
        conn = sqlite3.connect(PROJECT_DB)
        cursor = conn.cursor()
        
        has_requests = False
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provider_requests'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM provider_requests WHERE project_id = ?", (project_id,))
            if cursor.fetchone()[0] > 0:
                has_requests = True
                
        if not has_requests:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'")
            if cursor.fetchone():
                cursor.execute("""
                    SELECT SUM(input_tokens), SUM(output_tokens), SUM(cache_tokens),
                           SUM(thinking_tokens), SUM(total_tokens), SUM(estimated_cost_usd)
                    FROM usage_records
                    WHERE project_id = ?
                """, (project_id,))
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
            WHERE project_id = ?
        """, (project_id,))
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

def get_global_summary() -> dict:
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
        conn = sqlite3.connect(global_db)
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
    from context import parse_transcript
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usage_records'")
        if not cursor.fetchone():
            return
        
        cursor.execute("SELECT conversation_id, total_tokens FROM usage_records")
        rows = cursor.fetchall()
        for conv_id, total_tok in rows:
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
                # Scale down by 10 as correction factor
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
