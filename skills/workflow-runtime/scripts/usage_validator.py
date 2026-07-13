# usage_validator.py
import argparse
import sys
import os
import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from db import PROJECT_DB, init_db_schema
from reconciliation_engine import ReconciliationEngine, ReconciliationReport

class UsageValidator:
    def __init__(self, db_conn: sqlite3.Connection):
        self.db_conn = db_conn

    def validate(self) -> Dict[str, Any]:
        """Validate DB records for impossible value anomalies."""
        violations = []
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT request_id, provider, model, timestamp, input_tokens, output_tokens, total_tokens, cache_tokens, thinking_tokens, tool_tokens
                FROM provider_requests
            """)
            rows = cursor.fetchall()
            now_iso = datetime.now(timezone.utc).isoformat()
            
            for row in rows:
                req_id, provider, model, ts, inp, out, tot, cache, think, tool = row
                # 1. Negative checks
                for field_name, val in [("input_tokens", inp), ("output_tokens", out), ("total_tokens", tot),
                                       ("cache_tokens", cache), ("thinking_tokens", think), ("tool_tokens", tool)]:
                    if val is not None and val < 0:
                        violations.append({
                            "request_id": req_id,
                            "type": "negative_value",
                            "field": field_name,
                            "value": val,
                            "message": f"Negative value {val} in field {field_name}."
                        })
                # 2. total_tokens >= input_tokens + output_tokens
                if inp is not None and out is not None and tot is not None:
                    if tot < inp + out:
                        violations.append({
                            "request_id": req_id,
                            "type": "invalid_total",
                            "message": f"total_tokens ({tot}) is less than input ({inp}) + output ({out})."
                        })
                # 3. empty model
                if not model or not str(model).strip():
                    violations.append({
                        "request_id": req_id,
                        "type": "empty_model",
                        "message": "Model name is empty or whitespace."
                    })
                # 4. future timestamp
                if ts:
                    try:
                        # Simple string comparison is sufficient for ISO format or parse
                        if ts > now_iso:
                            violations.append({
                                "request_id": req_id,
                                "type": "future_timestamp",
                                "value": ts,
                                "message": f"Timestamp {ts} is in the future compared to current {now_iso}."
                            })
                    except Exception:
                        pass
        except Exception as e:
            return {"status": "error", "message": str(e), "violations": [], "count": 0}

        status = "violations" if violations else "ok"
        return {
            "status": status,
            "violations": violations,
            "count": len(violations)
        }

    def reconcile(self) -> Dict[str, Any]:
        """Delegate to ReconciliationEngine to perform a synchronization scan."""
        engine = ReconciliationEngine(self.db_conn)
        report = engine.sync()
        return report.to_dict()

    def doctor(self) -> Dict[str, Any]:
        """Perform system diagnostics and suggest actionable resolutions."""
        val_res = self.validate()
        violations = val_res.get("violations", [])
        suggestions = []
        
        # Impossible values analysis
        for v in violations:
            if v["type"] == "negative_value":
                suggestions.append({
                    "suggestion": f"Recalculate or clamp the negative value {v['value']} in {v['field']} for request {v['request_id']}.",
                    "action": "clamp_zero"
                })
            elif v["type"] == "invalid_total":
                suggestions.append({
                    "suggestion": f"Re-sum total_tokens to input + output for request {v['request_id']}.",
                    "action": "recompute_total"
                })
            elif v["type"] == "empty_model":
                suggestions.append({
                    "suggestion": f"Associate request {v['request_id']} with a fallback model name.",
                    "action": "set_fallback_model"
                })
            elif v["type"] == "future_timestamp":
                suggestions.append({
                    "suggestion": f"Reset request {v['request_id']} timestamp to current time.",
                    "action": "reset_timestamp"
                })

        # DB integrity checks
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()
            if integrity and integrity[0] != "ok":
                suggestions.append({
                    "suggestion": "Database integrity check failed. Run VACUUM or reconstruct DB.",
                    "action": "vacuum_db"
                })
        except Exception:
            pass

        # Compute confidence score
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT confidence_score FROM reconciliation_reports ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            score = row[0] if row else 1.0
        except Exception:
            score = 1.0

        return {
            "violations": violations,
            "suggestions": suggestions,
            "confidence_score": score
        }

    def diff(self, run_id_a: int, run_id_b: int) -> Dict[str, Any]:
        """Diff two reconciliation runs by ID."""
        engine = ReconciliationEngine(self.db_conn)
        report_a = engine.get_report_by_id(run_id_a)
        report_b = engine.get_report_by_id(run_id_b)
        
        if not report_a:
            return {"status": "error", "message": f"Run ID {run_id_a} not found."}
        if not report_b:
            return {"status": "error", "message": f"Run ID {run_id_b} not found."}

        dict_a = report_a.to_dict()
        dict_b = report_b.to_dict()
        
        delta = {}
        for key in ["requests_discovered", "requests_parsed", "duplicates_ignored", "corrupted_transcripts",
                    "missing_usage_metadata", "reconstructed_usage", "estimated_usage", "confidence_score", "duration_ms"]:
            delta[key] = dict_b[key] - dict_a[key]

        return {
            "delta": delta,
            "run_a": dict_a,
            "run_b": dict_b
        }

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="usage_validator",
        description="Usage Validator CLI for audit trails and anomalies (FEAT-049)"
    )
    parser.add_argument("--db", default=PROJECT_DB, help="Path to SQLite database")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparsers.add_parser("validate", help="Validate DB for value anomalies")
    subparsers.add_parser("reconcile", help="Sync and reconcile transcript history")
    subparsers.add_parser("doctor", help="Run diagnostic health-check and resolutions")
    
    diff_parser = subparsers.add_parser("diff", help="Diff two reconciliation runs")
    diff_parser.add_argument("--run-a", type=int, required=True, help="First run ID")
    diff_parser.add_argument("--run-b", type=int, required=True, help="Second run ID")

    args = parser.parse_args()

    # Ensure parent dir exists and DB initialized
    os.makedirs(os.path.dirname(os.path.abspath(args.db)), exist_ok=True)
    conn = sqlite3.connect(args.db)
    try:
        init_db_schema(conn)
        validator = UsageValidator(conn)
        
        if args.subcommand == "validate":
            res = validator.validate()
            print(json.dumps(res, ensure_ascii=False))
            return 1 if res.get("status") == "violations" else 0
            
        elif args.subcommand == "reconcile":
            res = validator.reconcile()
            print(json.dumps(res, ensure_ascii=False))
            return 0
            
        elif args.subcommand == "doctor":
            res = validator.doctor()
            print(json.dumps(res, ensure_ascii=False))
            return 0
            
        elif args.subcommand == "diff":
            res = validator.diff(args.run_a, args.run_b)
            if res.get("status") == "error":
                sys.stderr.write(res.get("message") + "\n")
                return 2
            print(json.dumps(res, ensure_ascii=False))
            return 0
    finally:
        conn.close()

if __name__ == "__main__":
    sys.exit(main())
