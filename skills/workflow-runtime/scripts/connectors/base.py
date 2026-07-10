# connectors/base.py
# ProviderConnector Abstract Base Class for FEAT-048
from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DetectedProvider:
    """Result of a provider detection attempt."""
    provider_name: str
    path: str
    version: str
    status: str  # "found" | "not_found" | "permission_error" | "error"
    error: Optional[str] = None


@dataclass
class DiagnosticsResult:
    """Per-provider diagnostics report entry."""
    provider_name: str
    status: str           # "connected" | "not_found" | "permission_error" | "stale" | "error"
    detected_path: Optional[str] = None
    last_parsed: Optional[str] = None  # ISO8601 or None
    error_message: Optional[str] = None
    accuracy_confidence: str = "unknown"  # "high" | "medium" | "low" | "unknown"


@dataclass
class NormalizedUsageRecord:
    """Provider-agnostic usage record. All providers map to this schema."""
    provider: str
    model: str
    conversation_id: str
    request_id: str
    timestamp: str                 # ISO8601
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    thinking_tokens: int
    total_tokens: int              # input + output (always computed, never trusted from raw)
    duration_ms: float
    estimated_cost_usd: float
    accuracy_source: str           # "provider_reported"|"transcript_parsed"|"derived"|"estimated"|"unknown"
    raw_payload: dict = field(default_factory=dict)
    
    # FEAT-049 new fields
    fingerprint: Optional[str] = None
    tool_tokens: int = 0
    transcript_offset: int = -1
    raw_metadata: Optional[dict] = field(default_factory=dict)

    def __post_init__(self):
        # Enforce: non-negative token counts FIRST (before computing total)
        for attr in ("input_tokens", "output_tokens", "cache_read_tokens",
                     "cache_write_tokens", "thinking_tokens", "tool_tokens"):
            try:
                if getattr(self, attr) < 0:
                    setattr(self, attr, 0)
            except TypeError:
                setattr(self, attr, 0)

        # Enforce: total_tokens always computed from clamped values
        self.total_tokens = self.input_tokens + self.output_tokens

        # Validate fingerprint format (must be 64-char lowercase hex or None)
        if self.fingerprint:
            import re
            if not re.match(r"^[0-9a-f]{64}$", self.fingerprint):
                self.fingerprint = None

        # Validate accuracy_source
        valid_sources = {
            "provider_reported", "transcript_parsed", "derived", "estimated",
            "response_payload", "api_metadata", "deterministic_reconstruction",
            "tokenizer", "unknown"
        }
        if self.accuracy_source not in valid_sources:
            self.accuracy_source = "unknown"

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "conversation_id": self.conversation_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_write_tokens": self.cache_write_tokens,
            "thinking_tokens": self.thinking_tokens,
            "total_tokens": self.total_tokens,
            "duration_ms": self.duration_ms,
            "estimated_cost_usd": self.estimated_cost_usd,
            "accuracy_source": self.accuracy_source,
            "raw_payload": self.raw_payload,
            "fingerprint": self.fingerprint,
            "tool_tokens": self.tool_tokens,
            "transcript_offset": self.transcript_offset,
            "raw_metadata": self.raw_metadata,
        }


class ProviderConnector(ABC):
    """
    Abstract base class for all provider connectors.

    Subclasses must implement detect(), discover_conversations(),
    parse_conversation(), and get_diagnostics().

    Contract:
    - detect() MUST NOT raise — return None on any failure
    - parse_conversation() returns empty list if no data found
    - get_diagnostics() always returns a DiagnosticsResult, never raises
    """

    def __init__(self, config: dict = None):
        """
        Args:
            config: Optional dict of path overrides and settings.
                    Keys: provider-specific (e.g. "brain_root", "log_path")
        """
        self._config = config or {}

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return canonical provider name (e.g. 'antigravity', 'claude_code')."""

    @abstractmethod
    def detect(self) -> Optional[DetectedProvider]:
        """
        Check if this provider is installed and accessible on the current system.

        Returns:
            DetectedProvider if found and readable, None otherwise.
            MUST NOT raise under any circumstances.
        """

    @abstractmethod
    def discover_conversations(self) -> List[str]:
        """
        Return list of conversation IDs available for this provider.

        Returns:
            List of conversation ID strings (may be empty).
        """

    @abstractmethod
    def parse_conversation(self, conv_id: str) -> List[NormalizedUsageRecord]:
        """
        Parse and normalize usage data for a given conversation.

        Args:
            conv_id: Conversation ID to parse.

        Returns:
            List of NormalizedUsageRecord (may be empty if no data found).
        """

    @abstractmethod
    def get_diagnostics(self) -> DiagnosticsResult:
        """
        Return current status, paths, and errors for diagnostics panel.

        Returns:
            DiagnosticsResult — always returned, never raises.
        """

    def _get_default_paths(self) -> List[str]:
        """
        Return OS-aware default paths for this provider.
        Subclasses override this to return their specific paths.

        Returns:
            List of candidate absolute paths in priority order.
        """
        return []

    def _resolve_path(self, env_var: str, default: str) -> str:
        """
        Resolve a path using env var override or default.

        Args:
            env_var: Environment variable name to check first.
            default: Default path if env var not set.

        Returns:
            Resolved absolute path string.
        """
        override = os.environ.get(env_var)
        if override and os.path.isabs(override):
            return override
        return os.path.expanduser(default)

    def _safe_exists(self, path: str) -> bool:
        """Check path existence without raising."""
        try:
            return os.path.exists(path)
        except Exception:
            return False

    def _safe_isdir(self, path: str) -> bool:
        """Check if path is a directory without raising."""
        try:
            return os.path.isdir(path)
        except Exception:
            return False


class ITranscriptParser(ABC):
    """
    Abstract interface for provider-specific transcript parsing with fingerprint.
    Does NOT inherit from ProviderConnector (separate interface; composed not inherited).
    """

    @abstractmethod
    def compute_fingerprint(self, raw_line: dict) -> str:
        """
        Compute SHA-256 fingerprint for a raw transcript entry.

        Args:
            raw_line: Raw JSON line dictionary.

        Returns:
            64-char fingerprint hex string.
        """
        pass

    @abstractmethod
    def extract_tool_tokens(self, raw_line: dict) -> int:
        """
        Extract tool call tokens from a raw transcript entry.

        Args:
            raw_line: Raw JSON line dictionary.

        Returns:
            Number of tool call tokens, 0 if unavailable.
        """
        pass

    @abstractmethod
    def get_usage_source(self, raw_line: dict) -> str:
        """
        Determine the accuracy source level for this entry.

        Args:
            raw_line: Raw JSON line dictionary.

        Returns:
            One of the valid accuracy_source strings.
        """
        pass

    @abstractmethod
    def parse_with_fingerprint(
        self,
        raw_line: dict,
        offset: int,
        fp_engine: "FingerprintEngine"
    ) -> Optional[NormalizedUsageRecord]:
        """
        Parse raw_line, compute fingerprint, check duplicates,
        and return a NormalizedUsageRecord or None if duplicate.

        Args:
            raw_line: Raw JSON line dictionary.
            offset: Byte offset in the transcript file.
            fp_engine: FingerprintEngine instance for duplicate checks.

        Returns:
            NormalizedUsageRecord v2 instance, or None if duplicate.
        """
        pass
