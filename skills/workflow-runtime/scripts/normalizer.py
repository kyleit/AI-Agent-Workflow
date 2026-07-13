# normalizer.py
# UsageNormalizer — maps provider-specific dicts to NormalizedUsageRecord
from __future__ import annotations

from typing import List

from connectors.base import NormalizedUsageRecord


class UsageNormalizer:
    """
    Maps provider-specific raw dicts to NormalizedUsageRecord.

    UsageNormalizer is stateless and can be used as a module-level singleton.

    Enforcement rules (from blueprint):
    - total_tokens always computed (input + output), never trusted from raw
    - accuracy_source immutable after construction
    - All token counts must be >= 0
    """

    def normalize(
        self,
        raw: dict,
        provider: str,
        accuracy_source: str = "unknown",
    ) -> NormalizedUsageRecord:
        """
        Map a provider-specific dict to NormalizedUsageRecord.

        Args:
            raw: Provider-specific usage dict.
            provider: Canonical provider name.
            accuracy_source: One of provider_reported|transcript_parsed|derived|estimated|unknown

        Returns:
            NormalizedUsageRecord dataclass instance.
        """
        if not isinstance(raw, dict):
            raw = {}

        return NormalizedUsageRecord(
            provider=str(provider),
            model=str(raw.get("model", "unknown")),
            conversation_id=str(raw.get("conversation_id", "")),
            request_id=str(raw.get("request_id", "")),
            timestamp=str(raw.get("timestamp", "")),
            input_tokens=self._to_int(raw.get("input_tokens", 0)),
            output_tokens=self._to_int(raw.get("output_tokens", 0)),
            cache_read_tokens=self._to_int(raw.get("cache_read_tokens", 0)),
            cache_write_tokens=self._to_int(raw.get("cache_write_tokens", 0)),
            thinking_tokens=self._to_int(raw.get("thinking_tokens", 0)),
            total_tokens=0,  # always recomputed in __post_init__
            duration_ms=self._to_float(raw.get("duration_ms", 0)),
            estimated_cost_usd=self._to_float(raw.get("estimated_cost_usd", 0.0)),
            accuracy_source=accuracy_source,
            raw_payload=raw,
        )

    def validate(self, record: NormalizedUsageRecord) -> List[str]:
        """
        Validate a NormalizedUsageRecord for required field presence and constraints.

        Args:
            record: Record to validate.

        Returns:
            List of validation error strings. Empty list = valid.
        """
        errors = []
        if not record.provider:
            errors.append("provider is required")
        if not record.conversation_id:
            errors.append("conversation_id is required")
        if not record.request_id:
            errors.append("request_id is required")
        if record.input_tokens < 0:
            errors.append("input_tokens must be >= 0")
        if record.output_tokens < 0:
            errors.append("output_tokens must be >= 0")
        if record.accuracy_source not in {
            "provider_reported", "transcript_parsed", "derived", "estimated", "unknown"
        }:
            errors.append(f"invalid accuracy_source: {record.accuracy_source!r}")
        return errors

    @staticmethod
    def _to_int(value) -> int:
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _to_float(value) -> float:
        try:
            return max(0.0, float(value or 0))
        except (TypeError, ValueError):
            return 0.0


# Module-level singleton
normalizer = UsageNormalizer()
