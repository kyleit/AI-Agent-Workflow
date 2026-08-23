from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any, Dict, cast

from workflow_runtime.application.workflow.reconciliation_engine import (
    ReconciliationEngine)
from workflow_runtime.infrastructure.persistence.db import (
    get_project_db_path, init_db_schema)


class UsageValidator:
    def __init__(self, db_conn: sqlite3.Connection) -> None:
        self.db_conn = db_conn

    def validate(self) -> Dict[str, Any]:
        """Validate DB records for impossible value anomalies."""
        violations: list[dict[str, Any]] = []
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT request_id, provider, model, timestamp, input_tokens, output_tokens, total_tokens, cache_tokens, thinking_tokens, tool_tokens
                FROM provider_requests
            """)
            rows = cursor.fetchall()
            now_iso = datetime.now(timezone.utc).isoformat()

            for row in rows:
                req_id, _provider, model, ts, inp, out, tot, cache, think, tool = row
                for field_name, val in [("input_tokens", inp), ("output_tokens", out), ("total_tokens", tot),
                                       ("cache_tokens", cache), ("thinking_tokens", think), ("tool_tokens", tool)]:
                    if val is not None and int(str(val)) < 0:
                        violations.append({
                            "request_id": req_id,
                            "type": "negative_value",
                            "field": field_name,
                            "value": val,
                            "message": f"Negative value {val} in field {field_name}."
                        })
                if inp is not None and out is not None and tot is not None:
                    if int(str(tot)) < int(str(inp)) + int(str(out)):
                        violations.append({
                            "request_id": req_id,
                            "type": "invalid_total",
                            "message": f"total_tokens ({tot}) is less than input ({inp}) + output ({out})."
                        })
                if not model or not str(model).strip():
                    violations.append({
                        "request_id": req_id,
                        "type": "empty_model",
                        "message": "Model name is empty or whitespace."
                    })
                if ts:
                    try:
                        if str(ts) > now_iso:
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
        raw_v = val_res.get("violations", [])
        violations: list[dict[str, Any]] = cast(list[dict[str, Any]], raw_v) if isinstance(raw_v, list) else []
        suggestions: list[dict[str, Any]] = []

        for v in violations:
            v_type = str(v.get("type", ""))
            v_req = str(v.get("request_id", ""))
            if v_type == "negative_value":
                suggestions.append({
                    "suggestion": f"Recalculate or clamp the negative value {v.get('value')} in {v.get('field')} for request {v_req}.",
                    "action": "clamp_zero"
                })
            elif v_type == "invalid_total":
                suggestions.append({
                    "suggestion": f"Re-sum total_tokens to input + output for request {v_req}.",
                    "action": "recompute_total"
                })
            elif v_type == "empty_model":
                suggestions.append({
                    "suggestion": f"Associate request {v_req} with a fallback model name.",
                    "action": "set_fallback_model"
                })
            elif v_type == "future_timestamp":
                suggestions.append({
                    "suggestion": f"Reset request {v_req} timestamp to current time.",
                    "action": "reset_timestamp"
                })

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

        score: float = 1.0
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT confidence_score FROM reconciliation_reports ORDER BY timestamp DESC LIMIT 1")
            row = cursor.fetchone()
            score = float(row[0]) if row else 1.0
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

        delta: dict[str, Any] = {}
        for key in ["requests_discovered", "requests_parsed", "duplicates_ignored", "corrupted_transcripts",
                    "missing_usage_metadata", "reconstructed_usage", "estimated_usage", "confidence_score", "duration_ms"]:
            delta[key] = float(dict_b[key]) - float(dict_a[key])

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
    parser.add_argument("--db", default=get_project_db_path(), help="Path to SQLite database")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    subparsers.add_parser("validate", help="Validate DB for value anomalies")
    subparsers.add_parser("reconcile", help="Sync and reconcile transcript history")
    subparsers.add_parser("doctor", help="Run diagnostic health-check and resolutions")

    diff_parser = subparsers.add_parser("diff", help="Diff two reconciliation runs")
    diff_parser.add_argument("--run-a", type=int, required=True, help="First run ID")
    diff_parser.add_argument("--run-b", type=int, required=True, help="Second run ID")

    args = parser.parse_args()

    db_path = str(args.db)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
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
            res = validator.diff(int(args.run_a), int(args.run_b))
            if res.get("status") == "error":
                sys.stderr.write(f"{res.get('message', '')}\n")
                return 2
            print(json.dumps(res, ensure_ascii=False))
            return 0
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
