from __future__ import annotations

import json
import os
import platform
import sqlite3
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, List, Optional, cast

if TYPE_CHECKING:
    from workflow_runtime.application.analysis.fingerprint_engine import FingerprintEngine

from workflow_runtime.infrastructure.connectors.base import (
    DetectedProvider, DiagnosticsResult, ITranscriptParser,
    NormalizedUsageRecord, ProviderConnector)

_PROVIDER_NAME = "vscode_agents"
_ENV_VAR = "VSCODE_LOGS_PATH"


def _default_log_paths() -> List[str]:
    """Return OS-aware default VS Code log directory paths."""
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        return [os.path.join(base, "Code", "logs")]
    elif system == "Darwin":
        return [os.path.expanduser("~/Library/Application Support/Code/logs")]
    else:
        return [
            os.path.expanduser("~/.config/Code/logs"),
            os.path.expanduser("~/.vscode/logs"),
        ]


class VSCodeAgentsConnector(ProviderConnector, ITranscriptParser):
    """
    Connector for VS Code AI Agents extension.

    Reads usage logs from VS Code log directories.
    Accuracy source: transcript_parsed
    """

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config or {})
        
        override = os.environ.get(_ENV_VAR)
        if override:
            self._log_paths = [override]
        else:
            self._log_paths = self._config.get("log_paths") or _default_log_paths()

    def get_provider_name(self) -> str:
        return _PROVIDER_NAME

    def detect(self) -> Optional[DetectedProvider]:
        try:
            for path in self._log_paths:
                if self._safe_isdir(path):
                    return DetectedProvider(
                        provider_name=_PROVIDER_NAME,
                        path=path,
                        version="1.0",
                        status="found",
                    )
            return DetectedProvider(
                provider_name=_PROVIDER_NAME,
                path=self._log_paths[0] if self._log_paths else "",
                version="",
                status="not_found",
            )
        except Exception as exc:
            return DetectedProvider(
                provider_name=_PROVIDER_NAME,
                path="",
                version="",
                status="error",
                error=str(exc),
            )

    def discover_conversations(self) -> List[str]:
        conv_ids: list[str] = []
        for log_dir in self._log_paths:
            if not self._safe_isdir(log_dir):
                continue
            try:
                for fname in os.listdir(log_dir):
                    if fname.endswith(".jsonl"):
                        conv_ids.append(fname.replace(".jsonl", ""))
            except (OSError, PermissionError):
                continue
        return conv_ids

    def parse_conversation(self, conv_id: str) -> List[NormalizedUsageRecord]:
        from workflow_runtime.application.analysis.fingerprint_engine import \
            FingerprintEngine
        from workflow_runtime.infrastructure.persistence.db import (
            get_project_db_path, init_db_schema)
        db_conn = sqlite3.connect(get_project_db_path())
        init_db_schema(db_conn)
        fp_engine = FingerprintEngine(db_conn)

        records: list[NormalizedUsageRecord] = []
        try:
            for log_dir in self._log_paths:
                log_file = os.path.join(log_dir, conv_id + ".jsonl")
                if not os.path.isfile(log_file):
                    continue
                try:
                    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                        for i, line in enumerate(f):
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                entry = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            if "conversation_id" not in entry:
                                entry["conversation_id"] = conv_id

                            record = self.parse_with_fingerprint(entry, i, fp_engine)
                            if record is not None:
                                records.append(record)
                except (IOError, PermissionError):
                    continue
        finally:
            db_conn.close()
        return records

    def get_diagnostics(self) -> DiagnosticsResult:
        for path in self._log_paths:
            if self._safe_isdir(path):
                return DiagnosticsResult(
                    provider_name=_PROVIDER_NAME,
                    status="connected",
                    detected_path=path,
                    accuracy_confidence="low",
                )
        return DiagnosticsResult(
            provider_name=_PROVIDER_NAME,
            status="not_found",
            detected_path=self._log_paths[0] if self._log_paths else "",
            error_message="VS Code log directory not found",
            accuracy_confidence="unknown",
        )

    # ------------------------------------------------------------------
    # ITranscriptParser Implementation
    # ------------------------------------------------------------------

    def compute_fingerprint(self, raw_line: dict[str, Any]) -> str:
        from workflow_runtime.application.analysis.fingerprint_engine import \
            FingerprintEngine
        fe = FingerprintEngine(None)
        rdict = raw_line
        usage = cast(dict[str, Any], rdict.get("usage") or {})
        fields: dict[str, Any] = {
            "provider": _PROVIDER_NAME,
            "conversation_id": str(rdict.get("conversation_id", "")),
            "request_id": str(rdict.get("request_id", "")),
            "response_id": str(rdict.get("response_id", "")),
            "model": str(rdict.get("model", "")),
            "timestamp": str(rdict.get("timestamp", "")),
            "raw_payload": usage
        }
        return fe.compute(fields)

    def extract_tool_tokens(self, raw_line: dict[str, Any]) -> int:
        usage = cast(dict[str, Any], raw_line.get("usage") or {})
        return int(usage.get("tool_tokens", 0) or 0)

    def get_usage_source(self, raw_line: dict[str, Any]) -> str:
        return "transcript_parsed"

    def parse_with_fingerprint(
        self,
        raw_line: dict[str, Any],
        offset: int,
        fp_engine: FingerprintEngine
    ) -> Optional[NormalizedUsageRecord]:
        rdict = raw_line
        conv_id = str(rdict.get("conversation_id", ""))
        fp = self.compute_fingerprint(rdict)

        # Check duplicate
        if fp_engine.is_duplicate(fp):
            fp_engine.register(fp, {
                "provider": _PROVIDER_NAME,
                "conversation_id": conv_id,
                "request_id": str(rdict.get("request_id", "")),
                "model": str(rdict.get("model", ""))
            })
            return None

        usage = cast(dict[str, Any], rdict.get("usage") or {})
        input_tokens = int(usage.get("promptTokens", 0) or usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("completionTokens", 0) or usage.get("output_tokens", 0) or 0)

        if input_tokens == 0 and output_tokens == 0:
            return None

        model = str(rdict.get("model", "vscode-copilot"))
        timestamp = str(rdict.get("timestamp") or datetime.now(timezone.utc).isoformat())
        request_id = str(rdict.get("request_id") or f"{conv_id}_{offset}")

        # Register new fingerprint
        metadata: dict[str, Any] = {
            "provider": _PROVIDER_NAME,
            "conversation_id": conv_id,
            "request_id": request_id,
            "model": model,
            "timestamp": timestamp
        }
        fp_engine.register(fp, metadata)

        return NormalizedUsageRecord(
            provider=_PROVIDER_NAME,
            model=model,
            conversation_id=conv_id,
            request_id=request_id,
            timestamp=timestamp,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=0,
            cache_write_tokens=0,
            thinking_tokens=0,
            total_tokens=0,
            duration_ms=float(rdict.get("duration", 0) or 0),
            estimated_cost_usd=0.0,
            accuracy_source="transcript_parsed",
            raw_payload=usage,
            fingerprint=fp,
            tool_tokens=self.extract_tool_tokens(rdict),
            transcript_offset=offset,
            raw_metadata=rdict
        )

    def _parse_entry(
        self, entry: dict[str, Any], conv_id: str, line_index: int
    ) -> Optional[NormalizedUsageRecord]:
        """Parse a VS Code AI agent log entry."""
        if "conversation_id" not in entry:
            entry["conversation_id"] = conv_id

        from workflow_runtime.application.analysis.fingerprint_engine import \
            FingerprintEngine
        dummy_engine = FingerprintEngine(sqlite3.connect(":memory:"))
        return self.parse_with_fingerprint(entry, line_index, dummy_engine)
