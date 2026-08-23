# cost_engine.py
# CostEngine — loads pricing.json and calculates per-request costs
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import date
from typing import Any, cast

from workflow_runtime.shared.usage_record import NormalizedUsageRecord

_DEFAULT_PRICING_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "pricing.json"
)


@dataclass
class CostBreakdown:
    """Detailed cost breakdown per token type."""
    input_cost: float = 0.0
    output_cost: float = 0.0
    cache_read_cost: float = 0.0
    cache_write_cost: float = 0.0
    thinking_cost: float = 0.0
    tool_cost: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.input_cost
            + self.output_cost
            + self.cache_read_cost
            + self.cache_write_cost
            + self.thinking_cost
            + self.tool_cost
        )


@dataclass
class ModelPricing:
    """Per-model pricing rates (USD per million tokens)."""
    input_per_mtok: float = 0.0
    output_per_mtok: float = 0.0
    cache_read_per_mtok: float = 0.0
    cache_write_per_mtok: float = 0.0
    thinking_per_mtok: float = 0.0
    tool_per_mtok: float = 0.0
    version: str = "1.0.0"


@dataclass
class CostResult:
    """Result of a cost calculation."""
    cost_usd: float
    breakdown: CostBreakdown
    model_matched: bool
    fallback_used: bool
    provider: str
    model: str
    pricing_version: str = ""


class CostEngine:
    """
    Load pricing.json and calculate per-request costs.

    Pricing data is loaded lazily on the first calculate() call and cached
    in memory for the lifetime of the CostEngine instance.

    If a provider/model combination is not found in pricing.json,
    the fallback rates are used and fallback_used=True is set in CostResult.
    """

    def __init__(self, pricing_path: str | None = None, db_conn: sqlite3.Connection | None = None) -> None:
        """
        Args:
            pricing_path: Absolute path to pricing.json.
                          Defaults to skills/workflow-runtime/data/pricing.json.
            db_conn: Optional sqlite3.Connection to query pricing_versions table.
        """
        self._pricing_path = os.path.abspath(
            pricing_path or _DEFAULT_PRICING_PATH
        )
        self._db_conn = db_conn
        self._data: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        """Load pricing.json (once). Returns empty dict on error."""
        if self._data is not None:
            return self._data
        try:
            with open(self._pricing_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self._data = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}
        except (IOError, json.JSONDecodeError):
            self._data = {}
        return self._data

    def get_pricing(self, provider: str, model: str) -> ModelPricing | None:
        """
        Return ModelPricing for a provider/model, or None if not found.

        Args:
            provider: Canonical provider name.
            model: Model identifier (e.g. 'gemini-2.5-flash').

        Returns:
            ModelPricing dataclass or None if not in pricing.json.
        """
        data = self._load()
        raw_provs = data.get("providers")
        providers = cast(dict[str, Any], raw_provs) if isinstance(raw_provs, dict) else {}
        raw_pdata = providers.get(provider)
        provider_data = cast(dict[str, Any], raw_pdata) if isinstance(raw_pdata, dict) else {}
        raw_models = provider_data.get("models")
        models = cast(dict[str, Any], raw_models) if isinstance(raw_models, dict) else {}
        raw_mdata = models.get(model)
        if not isinstance(raw_mdata, dict):
            return None
        model_data = cast(dict[str, Any], raw_mdata)
        return ModelPricing(
            input_per_mtok=float(model_data.get("input_per_mtok", 0)),
            output_per_mtok=float(model_data.get("output_per_mtok", 0)),
            cache_read_per_mtok=float(model_data.get("cache_read_per_mtok", 0)),
            cache_write_per_mtok=float(model_data.get("cache_write_per_mtok", 0)),
            thinking_per_mtok=float(model_data.get("thinking_per_mtok", 0)),
            tool_per_mtok=float(model_data.get("tool_per_mtok", 0)),
            version=str(model_data.get("version", "1.0.0")),
        )

    def get_pricing_version(self, provider: str, model: str, timestamp: str) -> str | None:
        """Lookup pricing_versions table for the version active at timestamp."""
        if not self._db_conn:
            return None
        try:
            cursor = self._db_conn.cursor()
            cursor.execute("""
                SELECT version FROM pricing_versions
                WHERE provider = ? AND model = ? AND effective_date <= ?
                ORDER BY effective_date DESC LIMIT 1
            """, (provider, model, timestamp[:10]))
            row = cursor.fetchone()
            if row:
                return str(row[0])
        except Exception:
            pass
        return None

    def lock_cost(self, conn: sqlite3.Connection, request_id: str, cost_result: CostResult, pricing_version: str) -> None:
        """Lock the calculated cost and pricing version into database."""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE provider_requests
                SET cost_usd = ?, pricing_version = ?
                WHERE request_id = ?
            """, (cost_result.cost_usd, pricing_version, request_id))
            conn.commit()
        except Exception:
            pass

    def calculate(
        self,
        provider: str | NormalizedUsageRecord,
        model: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        thinking_tokens: int = 0,
        tool_tokens: int = 0,
        request_timestamp: str | None = None,
        pricing_version: str | None = None,
    ) -> CostResult:
        """
        Calculate cost for a single request. Can accept a NormalizedUsageRecord or individual values.
        """
        provider_str = ""
        model_str = model or ""

        if isinstance(provider, NormalizedUsageRecord):
            rec = provider
            provider_str = str(rec.provider)
            model_str = str(rec.model)
            input_tokens = rec.input_tokens
            output_tokens = rec.output_tokens
            cache_read_tokens = int(getattr(rec, "cache_tokens", 0) or 0)
            cache_write_tokens = int(getattr(rec, "cache_write_tokens", 0) or 0)
            thinking_tokens = int(getattr(rec, "thinking_tokens", 0) or 0)
            tool_tokens = int(getattr(rec, "tool_tokens", 0) or 0)
            request_timestamp = str(getattr(rec, "timestamp", None) or "")
            pricing_version = pricing_version or getattr(rec, "pricing_version", None)
        else:
            provider_str = str(provider)

        pricing: ModelPricing | None = None
        fallback_used = False

        if self._db_conn and pricing_version:
            try:
                cursor = self._db_conn.cursor()
                cursor.execute("""
                    SELECT input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok, thinking_per_mtok, tool_per_mtok, version
                    FROM pricing_versions
                    WHERE provider = ? AND model = ? AND version = ?
                """, (provider_str, model_str, pricing_version))
                row = cursor.fetchone()
                if row:
                    pricing = ModelPricing(
                        input_per_mtok=float(row[0]),
                        output_per_mtok=float(row[1]),
                        cache_read_per_mtok=float(row[2]),
                        cache_write_per_mtok=float(row[3]),
                        thinking_per_mtok=float(row[4]),
                        tool_per_mtok=float(row[5]),
                        version=str(row[6])
                    )
            except Exception:
                pass

        if pricing is None and self._db_conn and request_timestamp:
            try:
                cursor = self._db_conn.cursor()
                cursor.execute("""
                    SELECT input_per_mtok, output_per_mtok, cache_read_per_mtok, cache_write_per_mtok, thinking_per_mtok, tool_per_mtok, version
                    FROM pricing_versions
                    WHERE provider = ? AND model = ? AND effective_date <= ?
                    ORDER BY effective_date DESC LIMIT 1
                """, (provider_str, model_str, request_timestamp[:10]))
                row = cursor.fetchone()
                if row:
                    pricing = ModelPricing(
                        input_per_mtok=float(row[0]),
                        output_per_mtok=float(row[1]),
                        cache_read_per_mtok=float(row[2]),
                        cache_write_per_mtok=float(row[3]),
                        thinking_per_mtok=float(row[4]),
                        tool_per_mtok=float(row[5]),
                        version=str(row[6])
                    )
                    pricing_version = str(row[6])
            except Exception:
                pass

        if pricing is None:
            pricing = self.get_pricing(provider_str, model_str)
            if pricing is not None:
                pricing_version = pricing_version or pricing.version
            else:
                fallback_used = True
                pricing = self._get_fallback()
                pricing_version = pricing_version or "fallback"

        def _cost(tokens: int, rate_per_mtok: float) -> float:
            return max(0.0, tokens * rate_per_mtok / 1_000_000)

        breakdown = CostBreakdown(
            input_cost=_cost(input_tokens or 0, pricing.input_per_mtok),
            output_cost=_cost(output_tokens or 0, pricing.output_per_mtok),
            cache_read_cost=_cost(cache_read_tokens, pricing.cache_read_per_mtok),
            cache_write_cost=_cost(cache_write_tokens, pricing.cache_write_per_mtok),
            thinking_cost=_cost(thinking_tokens, pricing.thinking_per_mtok),
            tool_cost=_cost(tool_tokens, pricing.tool_per_mtok),
        )

        return CostResult(
            cost_usd=round(breakdown.total, 8),
            breakdown=breakdown,
            model_matched=not fallback_used,
            fallback_used=fallback_used,
            provider=provider_str,
            model=model_str or "unknown",
            pricing_version=pricing_version or "1.0.0",
        )

    def is_stale(self, days: int = 30) -> bool:
        """
        Check if pricing.json is older than N days.
        """
        data = self._load()
        updated_str = data.get("updated_at", "")
        if not updated_str:
            return True
        try:
            updated = date.fromisoformat(str(updated_str)[:10])
            return (date.today() - updated).days > days
        except (ValueError, TypeError):
            return True

    def get_version(self) -> str:
        """Return the version string from pricing.json."""
        data = self._load()
        return str(data.get("version", "unknown"))

    def _get_fallback(self) -> ModelPricing:
        """Return fallback pricing rates from pricing.json."""
        data = self._load()
        raw_fb = data.get("fallback")
        fb = cast(dict[str, Any], raw_fb) if isinstance(raw_fb, dict) else {}
        return ModelPricing(
            input_per_mtok=float(fb.get("input_per_mtok", 1.50)),
            output_per_mtok=float(fb.get("output_per_mtok", 5.00)),
            cache_read_per_mtok=float(fb.get("cache_read_per_mtok", 0.375)),
            cache_write_per_mtok=float(fb.get("cache_write_per_mtok", 1.875)),
            thinking_per_mtok=float(fb.get("thinking_per_mtok", 5.00)),
            tool_per_mtok=float(fb.get("tool_per_mtok", 0.0)),
            version="fallback",
        )

    def to_dict(self, result: CostResult) -> dict[str, Any]:
        """Serialize a CostResult to a JSON-safe dict."""
        return {
            "cost_usd": result.cost_usd,
            "breakdown": {
                "input_cost": result.breakdown.input_cost,
                "output_cost": result.breakdown.output_cost,
                "cache_read_cost": result.breakdown.cache_read_cost,
                "cache_write_cost": result.breakdown.cache_write_cost,
                "thinking_cost": result.breakdown.thinking_cost,
                "tool_cost": result.breakdown.tool_cost,
            },
            "model_matched": result.model_matched,
            "fallback_used": result.fallback_used,
            "provider": result.provider,
            "model": result.model,
            "pricing_version": result.pricing_version,
        }


cost_engine = CostEngine()

__all__ = [
    "CostBreakdown",
    "ModelPricing",
    "CostResult",
    "CostEngine",
    "cost_engine",
]
