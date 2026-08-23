from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    raw_payload: dict[str, Any] = field(default_factory=dict[str, Any])

    # FEAT-049 new fields
    fingerprint: str | None = None
    tool_tokens: int = 0
    transcript_offset: int = -1
    raw_metadata: dict[str, Any] | None = field(default_factory=dict[str, Any])

    def __post_init__(self) -> None:
        for attr in ("input_tokens", "output_tokens", "cache_read_tokens",
                     "cache_write_tokens", "thinking_tokens", "tool_tokens"):
            try:
                val = int(getattr(self, attr))
                if val < 0:
                    setattr(self, attr, 0)
                else:
                    setattr(self, attr, val)
            except (TypeError, ValueError):
                setattr(self, attr, 0)

        self.total_tokens = self.input_tokens + self.output_tokens

        if self.fingerprint:
            import re
            if not re.match(r"^[0-9a-f]{64}$", self.fingerprint):
                self.fingerprint = None

        valid_sources = {
            "provider_reported", "transcript_parsed", "derived", "estimated",
            "response_payload", "api_metadata", "deterministic_reconstruction",
            "tokenizer", "unknown"
        }
        if self.accuracy_source not in valid_sources:
            self.accuracy_source = "unknown"

    def to_dict(self) -> dict[str, Any]:
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


__all__ = ["NormalizedUsageRecord"]
