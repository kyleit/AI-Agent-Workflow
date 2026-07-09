# budget_controller.py
import sqlite3
import os
import json
from datetime import datetime

PROJECT_DB = "workflow_usage.db"

def get_db_connection():
    return sqlite3.connect(PROJECT_DB)

def init_budget_tables():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budget_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        # Seed default policies if empty
        cursor.execute("SELECT COUNT(*) FROM budget_policies")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO budget_policies (provider, model, soft_warning_pct, high_usage_pct, critical_usage_pct, emergency_pct)
                VALUES ('antigravity', 'auto', 50.0, 70.0, 85.0, 95.0)
            """)
        # Seed default optimization mode
        cursor.execute("SELECT COUNT(*) FROM budget_settings WHERE key = 'optimization_mode'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO budget_settings (key, value) VALUES ('optimization_mode', 'auto')")
        conn.commit()
    finally:
        conn.close()

def get_budget_mode() -> str:
    init_budget_tables()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM budget_settings WHERE key = 'optimization_mode'")
        row = cursor.fetchone()
        return row[0] if row else "auto"
    except Exception:
        return "auto"
    finally:
        conn.close()

def set_budget_mode(mode: str) -> None:
    init_budget_tables()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO budget_settings (key, value) VALUES ('optimization_mode', ?)", (mode,))
        conn.commit()
    except Exception as e:
        print(f"Error setting budget mode: {e}")
    finally:
        conn.close()

def get_active_policy(provider="antigravity") -> dict:
    init_budget_tables()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT soft_warning_pct, high_usage_pct, critical_usage_pct, emergency_pct
            FROM budget_policies
            WHERE provider = ?
        """, (provider,))
        row = cursor.fetchone()
        if row:
            return {
                "soft_warning": row[0],
                "high_usage": row[1],
                "critical_usage": row[2],
                "emergency": row[3]
            }
        return {
            "soft_warning": 50.0,
            "high_usage": 70.0,
            "critical_usage": 85.0,
            "emergency": 95.0
        }
    finally:
        conn.close()

def get_optimization_strategies(current_pct: float) -> list[dict]:
    strategies = [
        {"name": "Remove duplicated workspace reads", "tokens_saved": 45000, "cost_saved": 0.02, "confidence": 0.95, "side_effects": "None", "min_pct": 50.0},
        {"name": "Remove duplicated tool results", "tokens_saved": 85000, "cost_saved": 0.04, "confidence": 0.90, "side_effects": "None", "min_pct": 50.0},
        {"name": "Reload from Project Memory", "tokens_saved": 150000, "cost_saved": 0.08, "confidence": 0.85, "side_effects": "Minor context refresh", "min_pct": 70.0},
        {"name": "Replace history with workflow summary", "tokens_saved": 350000, "cost_saved": 0.18, "confidence": 0.80, "side_effects": "Loses detailed chat history", "min_pct": 85.0},
        {"name": "Create a Resume Workflow checkpoint", "tokens_saved": 500000, "cost_saved": 0.25, "confidence": 0.99, "side_effects": "Requires workflow reload", "min_pct": 85.0},
        {"name": "Spawn a sub-agent for isolated work", "tokens_saved": 600000, "cost_saved": 0.30, "confidence": 0.75, "side_effects": "Spawns background task", "min_pct": 90.0}
    ]
    # Filter strategies by current percentage and order by tokens saved descending
    applicable = [s for s in strategies if current_pct >= s["min_pct"]]
    applicable.sort(key=lambda x: x["tokens_saved"], reverse=True)
    return applicable

def evaluate_budget(conversation_id: str, predicted_tokens: int, limit=2000000) -> dict:
    init_budget_tables()
    policy = get_active_policy()
    pct = (predicted_tokens / limit) * 100.0
    
    triggered = "Healthy"
    recommendations = []
    blocked = False
    
    if pct >= policy["emergency"]:
        triggered = "Emergency Protection"
        blocked = True
        recommendations = get_optimization_strategies(pct)
    elif pct >= policy["critical_usage"]:
        triggered = "Critical Usage"
        recommendations = get_optimization_strategies(pct)
    elif pct >= policy["high_usage"]:
        triggered = "High Usage"
        recommendations = get_optimization_strategies(pct)
    elif pct >= policy["soft_warning"]:
        triggered = "Soft Warning"
        recommendations = get_optimization_strategies(pct)
        
    mode = get_budget_mode()
    
    from db import get_workflow_summary
    wf_summary = get_workflow_summary(conversation_id, "antigravity", "auto")
    acc_cost = wf_summary.get("accumulated_usage", {}).get("estimated_cost_usd", 0.0)
    
    sim_without_tokens = predicted_tokens
    sim_without_cost = round(sim_without_tokens * 1.25 / 1000000, 4)
    
    savings_tokens = 0
    if recommendations:
        savings_tokens = recommendations[0]["tokens_saved"]
        
    sim_with_tokens = max(0, sim_without_tokens - savings_tokens)
    sim_with_cost = round(sim_with_tokens * 1.25 / 1000000, 4)
    savings_pct = round((savings_tokens / max(1, sim_without_tokens)) * 100, 1)
    
    return {
        "status": "blocked" if blocked else "approved",
        "predicted_pct": round(pct, 2),
        "policy_triggered": triggered,
        "recommendations": recommendations,
        "policy_thresholds": policy,
        "budget_mode": mode,
        "current_usage_usd": acc_cost,
        "predicted_next_tokens": predicted_tokens,
        "simulation": {
            "without_opt_tokens": sim_without_tokens,
            "without_opt_cost": sim_without_cost,
            "with_opt_tokens": sim_with_tokens,
            "with_opt_cost": sim_with_cost,
            "savings_pct": savings_pct
        }
    }

def apply_optimization(conversation_id: str, strategy_name: str, predicted_tokens: int) -> dict:
    init_budget_tables()
    strategies = get_optimization_strategies(99.0) # get all
    match = next((s for s in strategies if s["name"] == strategy_name), None)
    if not match:
        return {"status": "error", "message": f"Strategy '{strategy_name}' not found."}
        
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO budget_history (timestamp, conversation_id, predicted_tokens, policy_triggered, strategy_applied, tokens_saved, cost_saved, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().astimezone().isoformat(),
            conversation_id,
            predicted_tokens,
            "Manual",
            strategy_name,
            match["tokens_saved"],
            match["cost_saved"],
            "applied"
        ))
        conn.commit()
    finally:
        conn.close()
        
    return {
        "status": "success",
        "strategy": strategy_name,
        "tokens_saved": match["tokens_saved"],
        "cost_saved": match["cost_saved"]
    }

def get_budget_history(conversation_id: str) -> list[dict]:
    init_budget_tables()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, predicted_tokens, policy_triggered, strategy_applied, tokens_saved, cost_saved, status
            FROM budget_history
            WHERE conversation_id = ?
            ORDER BY timestamp DESC
        """, (conversation_id,))
        rows = cursor.fetchall()
        results = []
        for r in rows:
            results.append({
                "id": r[0],
                "timestamp": r[1],
                "predicted_tokens": r[2],
                "policy_triggered": r[3],
                "strategy_applied": r[4],
                "tokens_saved": r[5],
                "cost_saved": r[6],
                "status": r[7]
            })
        return results
    finally:
        conn.close()
