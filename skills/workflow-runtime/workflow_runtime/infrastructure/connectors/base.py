# connectors/base.py
# ProviderConnector Abstract Base Class for FEAT-048
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from workflow_runtime.application.analysis.fingerprint_engine import (
    FingerprintEngine)
from workflow_runtime.shared.usage_record import NormalizedUsageRecord


@dataclass
class DetectedProvider:
    """Result of a provider detection attempt."""
    provider_name: str
    path: str
    version: str
    status: str  # "found" | "not_found" | "permission_error" | "error"
    error: str | None = None


@dataclass
class DiagnosticsResult:
    """Per-provider diagnostics report entry."""
    provider_name: str
    status: str           # "connected" | "not_found" | "permission_error" | "stale" | "error"
    detected_path: str | None = None
    last_parsed: str | None = None  # ISO8601 or None
    error_message: str | None = None
    accuracy_confidence: str = "unknown"  # "high" | "medium" | "low" | "unknown"


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

    def __init__(self, config: dict[str, Any] | None = None) -> None:
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
    def detect(self) -> DetectedProvider | None:
        """
        Check if this provider is installed and accessible on the current system.

        Returns:
            DetectedProvider if found and readable, None otherwise.
            MUST NOT raise under any circumstances.
        """

    @abstractmethod
    def discover_conversations(self) -> list[str]:
        """
        Return list of conversation IDs available for this provider.

        Returns:
            List of conversation ID strings (may be empty).
        """

    @abstractmethod
    def parse_conversation(self, conv_id: str) -> list[NormalizedUsageRecord]:
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

    def _get_default_paths(self) -> list[str]:
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
    def compute_fingerprint(self, raw_line: dict[str, Any]) -> str:
        """
        Compute SHA-256 fingerprint for a raw transcript entry.

        Args:
            raw_line: Raw JSON line dictionary.

        Returns:
            64-char fingerprint hex string.
        """

    @abstractmethod
    def extract_tool_tokens(self, raw_line: dict[str, Any]) -> int:
        """
        Extract tool call tokens from a raw transcript entry.

        Args:
            raw_line: Raw JSON line dictionary.

        Returns:
            Number of tool call tokens, 0 if unavailable.
        """

    @abstractmethod
    def get_usage_source(self, raw_line: dict[str, Any]) -> str:
        """
        Determine the accuracy source level for this entry.

        Args:
            raw_line: Raw JSON line dictionary.

        Returns:
            One of the valid accuracy_source strings.
        """

    @abstractmethod
    def parse_with_fingerprint(
        self,
        raw_line: dict[str, Any],
        offset: int,
        fp_engine: FingerprintEngine
    ) -> NormalizedUsageRecord | None:
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


__all__ = [
    "DetectedProvider",
    "DiagnosticsResult",
    "ProviderConnector",
    "ITranscriptParser",
]
