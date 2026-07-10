# reconciliation_engine.py
import os
import sys
import json
import time
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from connectors import build_default_registry
from fingerprint_engine import FingerprintEngine
from connectors.base import NormalizedUsageRecord

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

    def to_dict(self) -> dict:
        return asdict(self)

class ReconciliationEngine:
    def __init__(self, db_conn: sqlite3.Connection, connector_registry=None):
        self.db_conn = db_conn
        self.registry = connector_registry or build_default_registry()
        self.fp_engine = FingerprintEngine(db_conn)

    def _discover_transcript_files(self) -> List[str]:
        """Discover all log files across all registered connectors."""
        files = []
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
        for conn in self.registry.list_connectors():
            log_paths = getattr(conn, "_log_paths", [])
            for p in log_paths:
                if os.path.isdir(p):
                    try:
                        for f in os.listdir(p):
                            if f.endswith(".jsonl") or f.endswith(".log"):
                                files.append(os.path.join(p, f))
                    except Exception:
                        pass
        # Deduplicate
        return list(set(os.path.abspath(f) for f in files))

    def _determine_provider(self, file_path: str) -> str:
        path_lower = file_path.lower()
        if "claude" in path_lower:
            return "claude_code"
        elif "cursor" in path_lower:
            return "cursor"
        elif "vscode" in path_lower:
            return "vscode_agents"
        else:
            return "antigravity"

    def sync(self, transcript_paths: List[str] = None) -> ReconciliationReport:
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

        records_to_insert = []

        for path in transcript_paths:
            if not os.path.isfile(path):
                continue
            provider = self._determine_provider(path)
            connector = self.registry.get_connector(provider)
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
                            rec = connector.parse_with_fingerprint(raw_line, current_offset, self.fp_engine)
                        except Exception:
                            corrupted += 1
                            continue

                        if rec is None:
                            # It could be a duplicate, or non-usage message turn
                            # Check if duplicate by fingerprint
                            fp = connector.compute_fingerprint(raw_line)
                            if self.fp_engine.is_duplicate(fp):
                                duplicates += 1
                            continue

                        # Success parsing NormalizedUsageRecord
                        parsed += 1
                        acc_source = getattr(rec, "accuracy_source", "estimated")
                        if acc_source == "deterministic_reconstruction":
                            reconstructed += 1
                        elif acc_source == "estimated":
                            estimated += 1
                        elif not acc_source or acc_source == "unknown":
                            missing += 1

                        # Compute cost
                        from cost_engine import CostEngine
                        cost_eng = CostEngine(db_conn=self.db_conn)
                        cost_res = cost_eng.calculate(rec)

                        # Build DB record dict
                        record_dict = {
                            "request_id": rec.request_id,
                            "workflow_id": getattr(rec, "workflow_id", "unknown") or "unknown",
                            "conversation_id": rec.conversation_id,
                            "project_id": os.path.basename(os.path.abspath(".")),
                            "skill_name": getattr(rec, "skill_name", "unknown") or "unknown",
                            "command_name": getattr(rec, "command_name", "unknown") or "unknown",
                            "model": rec.model,
                            "provider": rec.provider,
                            "timestamp": rec.timestamp,
                            "duration": getattr(rec, "duration_ms", 0.0) / 1000.0,
                            "input_tokens": rec.input_tokens,
                            "output_tokens": rec.output_tokens,
                            "cache_tokens": rec.cache_read_tokens,
                            "thinking_tokens": rec.thinking_tokens,
                            "total_tokens": rec.input_tokens + rec.output_tokens,
                            "cost_usd": cost_res.cost_usd,
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
                            "fingerprint": rec.fingerprint,
                            "pricing_version": cost_res.pricing_version,
                            "tool_tokens": rec.tool_tokens,
                            "transcript_offset": rec.transcript_offset,
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
                        r["status"], r["error_summary"], r["accuracy_source"], r["fingerprint"],
                        r["pricing_version"], r["tool_tokens"], r["transcript_offset"]
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
