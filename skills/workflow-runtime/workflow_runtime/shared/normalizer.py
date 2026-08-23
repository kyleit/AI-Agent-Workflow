from __future__ import annotations

from typing import Any

from workflow_runtime.shared.usage_record import NormalizedUsageRecord

# normalizer.py
# UsageNormalizer — maps provider-specific dicts to NormalizedUsageRecord



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
        raw: dict[str, Any],
        provider: str,
        accuracy_source: str = "unknown",
    ) -> NormalizedUsageRecord:
        """
        Map a provider-specific dict to NormalizedUsageRecord.
        """
        payload = raw

        return NormalizedUsageRecord(
            provider=str(provider),
            model=str(payload.get("model", "unknown")),
            conversation_id=str(payload.get("conversation_id", "")),
            request_id=str(payload.get("request_id", "")),
            timestamp=str(payload.get("timestamp", "")),
            input_tokens=self._to_int(payload.get("input_tokens", 0)),
            output_tokens=self._to_int(payload.get("output_tokens", 0)),
            cache_read_tokens=self._to_int(payload.get("cache_read_tokens", 0)),
            cache_write_tokens=self._to_int(payload.get("cache_write_tokens", 0)),
            thinking_tokens=self._to_int(payload.get("thinking_tokens", 0)),
            total_tokens=0,  # always recomputed in __post_init__
            duration_ms=self._to_float(payload.get("duration_ms", 0)),
            estimated_cost_usd=self._to_float(payload.get("estimated_cost_usd", 0.0)),
            accuracy_source=accuracy_source,
            raw_payload=payload,
        )

    def validate(self, record: NormalizedUsageRecord) -> list[str]:
        """
        Validate a NormalizedUsageRecord for required field presence and constraints.
        """
        errors: list[str] = []
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
    def _to_int(value: Any) -> int:
        try:
            val_str = str(value) if value is not None else "0"
            return max(0, int(float(val_str)))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            val_str = str(value) if value is not None else "0.0"
            return max(0.0, float(val_str))
        except (TypeError, ValueError):
            return 0.0


__all__ = ["UsageNormalizer"]
