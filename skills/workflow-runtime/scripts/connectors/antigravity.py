# connectors/antigravity.py
# AntigravityConnector — reads Antigravity IDE transcript.jsonl from BRAIN_ROOT
from __future__ import annotations

import json
import os
import sys
import hashlib
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from connectors.base import (
    DetectedProvider,
    DiagnosticsResult,
    NormalizedUsageRecord,
    ProviderConnector,
    ITranscriptParser,
)

# Default BRAIN_ROOT path
_DEFAULT_BRAIN_ROOT = os.path.join(
    os.path.expanduser("~"), ".gemini", "antigravity-ide", "brain"
)
_ENV_VAR = "ANTIGRAVITY_BRAIN_ROOT"
_TRANSCRIPT_REL = os.path.join(".system_generated", "logs", "transcript.jsonl")
_PROVIDER_NAME = "antigravity"


class AntigravityConnector(ProviderConnector, ITranscriptParser):
    """
    Connector for Antigravity IDE.

    Reads transcripts from:
      {BRAIN_ROOT}/{conversation_id}/.system_generated/logs/transcript.jsonl
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self._brain_root = self._config.get(
            "brain_root",
            self._resolve_path(_ENV_VAR, _DEFAULT_BRAIN_ROOT)
        )
        self._current_conv_id = ""
        self._accumulated_history_chars = 0
        self._current_model = "gemini-2.5-flash"

    def get_provider_name(self) -> str:
        return _PROVIDER_NAME

    def detect(self) -> Optional[DetectedProvider]:
        """Detect if Antigravity IDE is installed by checking BRAIN_ROOT."""
        try:
            if self._safe_isdir(self._brain_root):
                return DetectedProvider(
                    provider_name=_PROVIDER_NAME,
                    path=self._brain_root,
                    version="1.0",
                    status="found",
                )
            return DetectedProvider(
                provider_name=_PROVIDER_NAME,
                path=self._brain_root,
                version="",
                status="not_found",
            )
        except Exception as exc:
            return DetectedProvider(
                provider_name=_PROVIDER_NAME,
                path=self._brain_root,
                version="",
                status="error",
                error=str(exc),
            )

    def discover_conversations(self) -> List[str]:
        """Return all conversation IDs found in BRAIN_ROOT."""
        if not self._safe_isdir(self._brain_root):
            return []
        try:
            entries = []
            for name in os.listdir(self._brain_root):
                transcript = self._find_transcript_file(name)
                if transcript and os.path.isfile(transcript):
                    entries.append(name)
            return entries
        except Exception:
            return []

    def parse_conversation(self, conv_id: str) -> List[NormalizedUsageRecord]:
        """
        Parse usage data for a given conversation ID.
        """
        transcript_path = self._find_transcript_file(conv_id)
        if not transcript_path or not os.path.isfile(transcript_path):
            return []

        try:
            # We reset state for this conversation to parse sequentially
            self._current_conv_id = conv_id
            self._accumulated_history_chars = 0
            self._current_model = "gemini-2.5-flash"
            
            from fingerprint_engine import FingerprintEngine
            from db import PROJECT_DB, init_db_schema
            db_conn = sqlite3.connect(PROJECT_DB)
            init_db_schema(db_conn)
            dummy_engine = FingerprintEngine(db_conn)
            
            records = []
            try:
                with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
                    for i, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            entry = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        
                        rec = self.parse_with_fingerprint(entry, i, dummy_engine)
                        if rec is not None:
                            records.append(rec)
            finally:
                db_conn.close()
            return records
        except PermissionError:
            return []
        except Exception:
            return []

    def get_diagnostics(self) -> DiagnosticsResult:
        """Return diagnostics status for Antigravity provider."""
        if not self._safe_exists(self._brain_root):
            return DiagnosticsResult(
                provider_name=_PROVIDER_NAME,
                status="not_found",
                detected_path=self._brain_root,
                error_message="BRAIN_ROOT directory not found",
                accuracy_confidence="unknown",
            )
        if not self._safe_isdir(self._brain_root):
            return DiagnosticsResult(
                provider_name=_PROVIDER_NAME,
                status="error",
                detected_path=self._brain_root,
                error_message="BRAIN_ROOT path exists but is not a directory",
                accuracy_confidence="unknown",
            )
        # Check read permission
        try:
            os.listdir(self._brain_root)
        except PermissionError:
            return DiagnosticsResult(
                provider_name=_PROVIDER_NAME,
                status="permission_error",
                detected_path=self._brain_root,
                error_message="Permission denied reading BRAIN_ROOT",
                accuracy_confidence="unknown",
            )
        return DiagnosticsResult(
            provider_name=_PROVIDER_NAME,
            status="connected",
            detected_path=self._brain_root,
            last_parsed=datetime.now(timezone.utc).isoformat(),
            accuracy_confidence="high",
        )

    # ------------------------------------------------------------------
    # ITranscriptParser Implementation
    # ------------------------------------------------------------------

    def compute_fingerprint(self, raw_line: dict) -> str:
        from fingerprint_engine import FingerprintEngine
        fe = FingerprintEngine(None)
        
        # We need content hash to ensure uniqueness of model output
        content = raw_line.get("content", "") or ""
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        
        fields = {
            "provider": _PROVIDER_NAME,
            "conversation_id": raw_line.get("conversation_id", ""),
            "request_id": str(raw_line.get("step_index", "") or ""),
            "response_id": "",
            "model": raw_line.get("model", ""),
            "timestamp": raw_line.get("timestamp") or raw_line.get("created_at") or "",
            "raw_payload": {
                "type": raw_line.get("type", ""),
                "source": raw_line.get("source", ""),
                "content_hash": content_hash
            }
        }
        return fe.compute(fields)

    def extract_tool_tokens(self, raw_line: dict) -> int:
        # Antigravity does not report tool call tokens explicitly
        return 0

    def get_usage_source(self, raw_line: dict) -> str:
        # Check if actual usage metrics are in step
        usage = raw_line.get("usage") or {}
        content = raw_line.get("content")
        if isinstance(content, dict):
            usage = usage or content.get("usage") or {}
        return "transcript_parsed" if usage else "estimated"

    def parse_with_fingerprint(
        self,
        raw_line: dict,
        offset: int,
        fp_engine: "FingerprintEngine"
    ) -> Optional[NormalizedUsageRecord]:
        if not isinstance(raw_line, dict):
            return None

        # Track conversation ID changes
        conv_id = raw_line.get("conversation_id", "") or self._current_conv_id
        if "conversation_id" not in raw_line:
            raw_line["conversation_id"] = conv_id

        if conv_id != self._current_conv_id:
            self._current_conv_id = conv_id
            self._accumulated_history_chars = 0
            self._current_model = "gemini-2.5-flash"

        content = raw_line.get("content", "") or ""
        step_type = raw_line.get("type", "")
        source = raw_line.get("source", "")
        
        # Detect model change
        if step_type == "USER_INPUT" and "Model Selection" in content:
            import re
            match = re.search(r"Model Selection` from \S+ to ([^\.]+)", content)
            if match:
                model_name = match.group(1).strip()
                self._current_model = model_name.lower().replace(" ", "-")

        # Process model response turns
        if source == "MODEL" and step_type in ("PLANNER_RESPONSE", "ASK_QUESTION"):
            # Update step dictionary for fingerprinting
            raw_line["model"] = self._current_model
            fp = self.compute_fingerprint(raw_line)
            
            # Check duplicate
            if fp_engine.is_duplicate(fp):
                fp_engine.register(fp, {
                    "provider": _PROVIDER_NAME,
                    "conversation_id": conv_id,
                    "request_id": str(raw_line.get("step_index", "") or ""),
                    "model": self._current_model
                })
                # Advance history even on duplicate to keep alignment
                self._accumulated_history_chars += len(content)
                return None

            # 1. First try parser based on provider-reported usage in step
            parsed_rec = self._parse_step(raw_line, conv_id)
            if parsed_rec is not None:
                # Add fingerprint and offset metadata
                parsed_rec.fingerprint = fp
                parsed_rec.transcript_offset = offset
                parsed_rec.raw_metadata = raw_line
                
                # Register fingerprint
                fp_engine.register(fp, {
                    "provider": _PROVIDER_NAME,
                    "conversation_id": conv_id,
                    "request_id": parsed_rec.request_id,
                    "model": parsed_rec.model,
                    "timestamp": parsed_rec.timestamp
                })
                self._accumulated_history_chars += len(content)
                return parsed_rec

            # 2. Fallback to estimation based on char counting
            input_chars = self._accumulated_history_chars
            thinking = raw_line.get("thinking", "") or ""
            thinking_chars = len(thinking)
            
            output_chars = len(content) + thinking_chars
            tool_calls = raw_line.get("tool_calls", []) or []
            if tool_calls:
                output_chars += len(json.dumps(tool_calls))
                
            input_tokens = max(0, int(input_chars / 3))
            output_tokens = max(0, int(output_chars / 3))
            thinking_tokens = max(0, int(thinking_chars / 3))
            cache_read = int(input_tokens * 0.15)
            
            timestamp = raw_line.get("timestamp") or raw_line.get("created_at") or datetime.now(timezone.utc).isoformat()
            request_id = raw_line.get("request_id") or f"{conv_id}_{raw_line.get('step_index', offset)}"
            
            # Register fingerprint
            metadata = {
                "provider": _PROVIDER_NAME,
                "conversation_id": conv_id,
                "request_id": request_id,
                "model": self._current_model,
                "timestamp": timestamp
            }
            fp_engine.register(fp, metadata)
            
            rec = NormalizedUsageRecord(
                provider=_PROVIDER_NAME,
                model=self._current_model,
                conversation_id=conv_id,
                request_id=request_id,
                timestamp=str(timestamp),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cache_read_tokens=cache_read,
                cache_write_tokens=0,
                thinking_tokens=thinking_tokens,
                total_tokens=0,
                duration_ms=float(raw_line.get("duration_ms", 0) or 0),
                estimated_cost_usd=0.0,
                accuracy_source="estimated",
                raw_payload={
                    "total_input_chars": input_chars,
                    "total_output_chars": output_chars,
                    "thinking_chars": thinking_chars
                },
                fingerprint=fp,
                tool_tokens=0,
                transcript_offset=offset,
                raw_metadata=raw_line
            )
            
            self._accumulated_history_chars += len(content)
            return rec
        else:
            self._accumulated_history_chars += len(content)
            return None

    def _find_transcript_file(self, conv_id: str) -> Optional[str]:
        """Construct transcript file path for a given conversation ID."""
        if not conv_id:
            return None
        path = os.path.join(self._brain_root, conv_id, _TRANSCRIPT_REL)
        return path

    def _read_jsonl(self, file_path: str) -> List[dict]:
        """Read all lines from a JSONL file, skipping malformed entries."""
        lines = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        lines.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except (IOError, OSError):
            pass
        return lines

    def _parse_step(self, step: dict, conv_id: str) -> Optional[NormalizedUsageRecord]:
        """
        Extract NormalizedUsageRecord from a single transcript step.
        """
        if not isinstance(step, dict):
            return None

        step_type = step.get("type", "")
        if step_type not in ("PLANNER_RESPONSE", "MODEL_RESPONSE"):
            return None

        # Try to extract usage data
        usage = step.get("usage") or {}
        content = step.get("content")
        if isinstance(content, dict):
            usage = usage or content.get("usage") or {}

        input_tokens = int(usage.get("input_tokens", 0) or 0)
        output_tokens = int(usage.get("output_tokens", 0) or 0)
        cache_read = int(usage.get("cache_read_input_tokens", 0) or 0)
        cache_write = int(usage.get("cache_creation_input_tokens", 0) or 0)
        thinking = int(usage.get("thinking_tokens", 0) or 0)

        # Skip steps with no token data
        if input_tokens == 0 and output_tokens == 0:
            return None

        # Extract model
        model = (
            step.get("model")
            or step.get("metadata", {}).get("model")
            or self._current_model
        )

        # Extract timestamp
        timestamp = (
            step.get("timestamp")
            or step.get("created_at")
            or datetime.now(timezone.utc).isoformat()
        )

        step_index = step.get("step_index", 0)
        request_id = f"{conv_id}_{step_index}"

        return NormalizedUsageRecord(
            provider=_PROVIDER_NAME,
            model=str(model),
            conversation_id=conv_id,
            request_id=request_id,
            timestamp=str(timestamp),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            cache_write_tokens=cache_write,
            thinking_tokens=thinking,
            total_tokens=0,
            duration_ms=float(step.get("duration_ms", 0) or 0),
            estimated_cost_usd=0.0,
            accuracy_source="transcript_parsed",
            raw_payload=usage,
        )
