from __future__ import annotations

import json
import os
import sqlite3
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Optional, cast

# from workflow_runtime.infrastructure.connectors import build_default_registry
from workflow_runtime.application.analysis.fingerprint_engine import \
    FingerprintEngine
from workflow_runtime.application.ports.locator import InfrastructureLocator

# from workflow_runtime.infrastructure.connectors.base import NormalizedUsageRecord

@dataclass
class ReconciliationReport:
    report_id: Optional[int]
    timestamp: str
    requests_discovered: int
    requests_parsed: int
    duplicates_ignored: int
    corrupted_transcripts: int
    missing_usage_metadata: int
    reconstructed_usage: int
    estimated_usage: int
    confidence_score: float
    duration_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class ReconciliationEngine:
    def __init__(self, db_conn: sqlite3.Connection, connector_registry: Any = None):
        self.db_conn = db_conn
        if connector_registry:
            self.registry: Any = connector_registry
        elif hasattr(InfrastructureLocator, "get_connector_registry"):
            self.registry = getattr(InfrastructureLocator, "get_connector_registry")()
        else:
            self.registry = None
        self.fp_engine = FingerprintEngine(db_conn)

    def _discover_transcript_files(self) -> list[str]:
        """Discover all log files across all registered connectors."""
        files: list[str] = []
        # 1. Check Antigravity (main brain workspace)
        # Look for transcript.jsonl under current workspace or environment
        brain_root = os.environ.get("BRAIN_ROOT")
        if brain_root and os.path.isdir(brain_root):
            for root, _, filenames in os.walk(brain_root):
                for f in filenames:
                    if f == "transcript.jsonl":
                        files.append(os.path.join(root, f))

        # Also check local .system_generated/logs/transcript.jsonl
        local_logs = os.path.join(".system_generated", "logs", "transcript.jsonl")
        if os.path.isfile(local_logs):
            files.append(local_logs)

        # 2. Check other connectors log directories
        if self.registry and hasattr(self.registry, "list_connectors"):
            for conn in cast(list[Any], getattr(self.registry, "list_connectors")()):
                log_paths: list[str] = cast(list[str], getattr(conn, "_log_paths", []))
                for p in log_paths:
                    if os.path.isdir(p):
                        try:
                            for fname_raw in os.listdir(p):
                                f_str = str(fname_raw)
                                if f_str.endswith(".jsonl") or f_str.endswith(".log"):
                                    files.append(os.path.join(p, f_str))
                        except Exception:
                            pass
        # Deduplicate
        return list(set(os.path.abspath(f) for f in files))

    def _determine_provider(self, file_path: str) -> str:
        return self._infer_connector_name(file_path)

    def _infer_connector_name(self, filepath: str) -> str:
        path_lower = filepath.lower()
        if "claude" in path_lower:
            return "claude_code"
        elif "cursor" in path_lower:
            return "cursor"
        elif "vscode" in path_lower:
            return "vscode_agents"
        else:
            return "antigravity"

    def sync(self, transcript_paths: list[str] | None = None) -> ReconciliationReport:
        """Runs the reconciliation sync and returns the report. Idempotent."""
        start_time = time.time()

        if transcript_paths is None:
            transcript_paths = self._discover_transcript_files()

        discovered = 0
        parsed = 0
        duplicates = 0
        corrupted = 0
        missing = 0
        reconstructed = 0
        estimated = 0

        # Enable WAL mode
        try:
            self.db_conn.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass

        records_to_insert: list[dict[str, Any]] = []

        for path in transcript_paths:
            if not os.path.isfile(path):
                continue
            provider = self._determine_provider(path)
            connector: Any = getattr(self.registry, "get_connector")(provider) if self.registry and hasattr(self.registry, "get_connector") else None
            if not connector:
                continue

            try:
                # Open file in binary mode to track byte offsets correctly
                with open(path, "rb") as f:
                    offset = 0
                    while True:
                        line_bytes = f.readline()
                        if not line_bytes:
                            break

                        discovered += 1
                        line_str = line_bytes.decode("utf-8", errors="replace").strip()
                        current_offset = offset
                        offset += len(line_bytes)

                        if not line_str:
                            continue

                        try:
                            raw_line = json.loads(line_str)
                        except json.JSONDecodeError:
                            corrupted += 1
                            continue

                        # Parse using connector's parse_with_fingerprint
                        try:
                            rec_parse_fn: Any = getattr(connector, "parse_with_fingerprint", None)
                            rec = rec_parse_fn(raw_line, current_offset, self.fp_engine) if callable(rec_parse_fn) else None
                        except Exception:
                            corrupted += 1
                            continue

                        if rec is None:
                            try:
                                fp_fn: Any = getattr(connector, "compute_fingerprint", None)
                                fp = str(fp_fn(raw_line)) if callable(fp_fn) else ""
                                if fp and self.fp_engine.is_duplicate(fp):
                                    duplicates += 1
                            except Exception:
                                pass
                            continue

                        # Success parsing InfrastructureLocator.NormalizedUsageRecord
                        parsed += 1
                        acc_source = getattr(rec, "accuracy_source", "estimated")
                        if acc_source == "deterministic_reconstruction":
                            reconstructed += 1
                        elif acc_source == "estimated":
                            estimated += 1
                        elif not acc_source or acc_source == "unknown":
                            missing += 1

                        # Compute cost
                        from workflow_runtime.application.analytics.cost_engine import \
                            CostEngine
                        cost_eng = CostEngine(db_conn=self.db_conn)
                        cost_res = cost_eng.calculate(cast(Any, rec))

                        # Build DB record dict
                        rec_obj = cast(Any, rec)
                        cost_obj = cast(Any, cost_res)
                        input_toks = cast(int, getattr(rec_obj, "input_tokens", 0))
                        output_toks = cast(int, getattr(rec_obj, "output_tokens", 0))
                        record_dict: dict[str, Any] = {
                            "request_id": getattr(rec_obj, "request_id", ""),
                            "workflow_id": getattr(rec_obj, "workflow_id", "unknown") or "unknown",
                            "conversation_id": getattr(rec_obj, "conversation_id", ""),
                            "project_id": os.path.basename(os.path.abspath(".")),
                            "skill_name": getattr(rec_obj, "skill_name", "unknown") or "unknown",
                            "command_name": getattr(rec_obj, "command_name", "unknown") or "unknown",
                            "model": getattr(rec_obj, "model", ""),
                            "provider": getattr(rec_obj, "provider", ""),
                            "timestamp": getattr(rec_obj, "timestamp", ""),
                            "duration": float(getattr(rec_obj, "duration_ms", 0.0)) / 1000.0,
                            "input_tokens": input_toks,
                            "output_tokens": output_toks,
                            "cache_tokens": getattr(rec_obj, "cache_read_tokens", 0),
                            "thinking_tokens": getattr(rec_obj, "thinking_tokens", 0),
                            "total_tokens": input_toks + output_toks,
                            "cost_usd": getattr(cost_obj, "cost_usd", 0.0),
                            "tool_call_count": 0,
                            "workspace_read_count": 0,
                            "memory_hit_count": 0,
                            "rag_hit_count": 0,
                            "context_usage_percentage": 0.0,
                            "context_limit_tokens": 1000000,
                            "context_breakdown_json": "{}",
                            "status": "success",
                            "error_summary": None,
                            "accuracy_source": acc_source,
                            "fingerprint": getattr(rec_obj, "fingerprint", ""),
                            "pricing_version": getattr(cost_obj, "pricing_version", ""),
                            "tool_tokens": getattr(rec_obj, "tool_tokens", 0),
                            "transcript_offset": getattr(rec_obj, "transcript_offset", -1),
                        }
                        records_to_insert.append(record_dict)

            except Exception:
                corrupted += 1

        # Perform batch insert directly into self.db_conn
        if records_to_insert:
            try:
                cursor = self.db_conn.cursor()
                cursor.executemany("""
                    INSERT OR IGNORE INTO provider_requests (
                        request_id, workflow_id, conversation_id, project_id, skill_name, command_name,
                        model, provider, timestamp, duration, input_tokens, output_tokens, cache_tokens,
                        thinking_tokens, total_tokens, cost_usd, tool_call_count, workspace_read_count,
                        memory_hit_count, rag_hit_count, context_usage_percentage, context_limit_tokens,
                        context_breakdown_json, status, error_summary, accuracy_source, fingerprint,
                        pricing_version, tool_tokens, transcript_offset
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    (
                        r["request_id"], r["workflow_id"], r["conversation_id"], r["project_id"],
                        r["skill_name"], r["command_name"], r["model"], r["provider"], r["timestamp"],
                        r["duration"], r["input_tokens"], r["output_tokens"], r["cache_tokens"],
                        r["thinking_tokens"], r["total_tokens"], r["cost_usd"], r["tool_call_count"],
                        r["workspace_read_count"], r["memory_hit_count"], r["rag_hit_count"],
                        r["context_usage_percentage"], r["context_limit_tokens"], r["context_breakdown_json"],
                        r.get("status"), r.get("error_summary"), r.get("accuracy_source"), r.get("fingerprint"),
                        r.get("pricing_version"), r.get("tool_tokens"), r.get("transcript_offset")
                    )
                    for r in records_to_insert
                ])
                self.db_conn.commit()
            except Exception:
                pass

        # Compute confidence score
        total_valid = parsed
        total_invalid = corrupted + missing
        if total_valid + total_invalid > 0:
            confidence = total_valid / float(total_valid + total_invalid)
        else:
            confidence = 1.0

        duration = int((time.time() - start_time) * 1000)

        report = ReconciliationReport(
            report_id=None,
            timestamp=datetime.now(timezone.utc).isoformat(),
            requests_discovered=discovered,
            requests_parsed=parsed,
            duplicates_ignored=duplicates,
            corrupted_transcripts=corrupted,
            missing_usage_metadata=missing,
            reconstructed_usage=reconstructed,
            estimated_usage=estimated,
            confidence_score=round(confidence, 4),
            duration_ms=duration
        )

        # Persist report to database
        report_id = self._persist_report(report)
        report.report_id = report_id

        return report

    def _persist_report(self, report: ReconciliationReport) -> int:
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO reconciliation_reports (
                    timestamp, requests_discovered, requests_parsed, duplicates_ignored,
                    corrupted_transcripts, missing_usage_metadata, reconstructed_usage,
                    estimated_usage, confidence_score, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report.timestamp,
                report.requests_discovered,
                report.requests_parsed,
                report.duplicates_ignored,
                report.corrupted_transcripts,
                report.missing_usage_metadata,
                report.reconstructed_usage,
                report.estimated_usage,
                report.confidence_score,
                report.duration_ms
            ))
            self.db_conn.commit()
            return cursor.lastrowid or 0
        except Exception:
            return 0

    def get_last_report(self) -> Optional[ReconciliationReport]:
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, requests_discovered, requests_parsed, duplicates_ignored,
                       corrupted_transcripts, missing_usage_metadata, reconstructed_usage,
                       estimated_usage, confidence_score, duration_ms
                FROM reconciliation_reports
                ORDER BY timestamp DESC LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return ReconciliationReport(*row)
        except Exception:
            pass
        return None

    def get_report_by_id(self, report_id: int) -> Optional[ReconciliationReport]:
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, requests_discovered, requests_parsed, duplicates_ignored,
                       corrupted_transcripts, missing_usage_metadata, reconstructed_usage,
                       estimated_usage, confidence_score, duration_ms
                FROM reconciliation_reports
                WHERE id = ?
            """, (report_id,))
            row = cursor.fetchone()
            if row:
                return ReconciliationReport(*row)
        except Exception:
            pass
        return None
