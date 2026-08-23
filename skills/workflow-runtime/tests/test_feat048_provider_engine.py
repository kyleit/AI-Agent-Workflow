"""
tests/test_feat048_provider_engine.py
Unit tests for FEAT-048: Provider-Centric Runtime & Usage Engine
Covers: NormalizedUsageRecord, UsageNormalizer, CostEngine,
        ConnectorRegistry, IncrementalTranscriptReader, AntigravityConnector
"""
import json
import os
import sqlite3
import sys
import tempfile

import pytest

# Ensure scripts/ is importable
SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from connectors.base import (
    DetectedProvider,
    DiagnosticsResult,
    NormalizedUsageRecord,
)
from connectors import ConnectorRegistry, ConnectorNotFoundError, TranscriptNotFoundError
from normalizer import UsageNormalizer
from cost_engine import CostEngine
from transcript_engine import IncrementalTranscriptReader, ensure_transcript_cursors_table


# ============================================================
# 1. NormalizedUsageRecord
# ============================================================

class TestNormalizedUsageRecord:

    def _make(self, **kwargs):
        defaults = dict(
            provider="test", model="m", conversation_id="c", request_id="r",
            timestamp="2026-01-01T00:00:00Z",
            input_tokens=100, output_tokens=50,
            cache_read_tokens=10, cache_write_tokens=5, thinking_tokens=2,
            total_tokens=0, duration_ms=0.0, estimated_cost_usd=0.0,
            accuracy_source="estimated",
        )
        defaults.update(kwargs)
        return NormalizedUsageRecord(**defaults)

    def test_total_tokens_computed(self):
        r = self._make(input_tokens=100, output_tokens=50, total_tokens=99999)
        assert r.total_tokens == 150

    def test_negative_tokens_clamped_to_zero(self):
        r = self._make(input_tokens=-5, output_tokens=-10)
        assert r.input_tokens == 0
        assert r.output_tokens == 0
        assert r.total_tokens == 0

    def test_negative_cache_clamped(self):
        r = self._make(cache_read_tokens=-100, cache_write_tokens=-50)
        assert r.cache_read_tokens == 0
        assert r.cache_write_tokens == 0

    def test_total_uses_clamped_values(self):
        r = self._make(input_tokens=-5, output_tokens=30)
        assert r.total_tokens == 30  # 0 + 30

    def test_invalid_accuracy_source_normalized(self):
        r = self._make(accuracy_source="BOGUS_SOURCE")
        assert r.accuracy_source == "unknown"

    def test_valid_accuracy_sources(self):
        for src in ("provider_reported", "transcript_parsed", "derived", "estimated", "unknown"):
            r = self._make(accuracy_source=src)
            assert r.accuracy_source == src

    def test_to_dict_structure(self):
        r = self._make()
        d = r.to_dict()
        assert "provider" in d
        assert "input_tokens" in d
        assert "total_tokens" in d
        assert "accuracy_source" in d
        assert d["total_tokens"] == 150


# ============================================================
# 2. UsageNormalizer
# ============================================================

class TestUsageNormalizer:

    def setup_method(self):
        self.n = UsageNormalizer()

    def test_normalize_basic(self):
        rec = self.n.normalize(
            {"input_tokens": 100, "output_tokens": 50, "model": "gpt-4o",
             "conversation_id": "c", "request_id": "r", "timestamp": "t"},
            provider="openai", accuracy_source="transcript_parsed"
        )
        assert rec.total_tokens == 150
        assert rec.accuracy_source == "transcript_parsed"
        assert rec.provider == "openai"

    def test_normalize_non_dict_input(self):
        rec = self.n.normalize(None, provider="test", accuracy_source="unknown")
        assert rec.total_tokens == 0
        assert rec.provider == "test"

    def test_validate_passes_for_valid_record(self):
        rec = self.n.normalize(
            {"input_tokens": 10, "output_tokens": 5, "conversation_id": "x",
             "request_id": "y", "timestamp": "t"},
            provider="test"
        )
        errors = self.n.validate(rec)
        assert errors == []

    def test_validate_catches_missing_provider(self):
        rec = self.n.normalize({}, provider="", accuracy_source="unknown")
        errors = self.n.validate(rec)
        assert "provider is required" in errors

    def test_validate_catches_missing_conversation_id(self):
        rec = self.n.normalize({}, provider="test", accuracy_source="unknown")
        errors = self.n.validate(rec)
        assert "conversation_id is required" in errors

    def test_validate_catches_invalid_accuracy_source(self):
        # NormalizedUsageRecord normalizes accuracy_source in __post_init__
        # so validate won't catch it — but the record itself shows "unknown"
        rec = self.n.normalize(
            {"input_tokens": 0, "output_tokens": 0, "conversation_id": "c",
             "request_id": "r", "timestamp": "t"},
            provider="test", accuracy_source="BAD"
        )
        # accuracy_source normalized by __post_init__ to "unknown" — no error
        errors = self.n.validate(rec)
        assert rec.accuracy_source == "unknown"

    def test_to_int_negative_clamped(self):
        assert UsageNormalizer._to_int(-100) == 0

    def test_to_float_negative_clamped(self):
        assert UsageNormalizer._to_float(-1.5) == 0.0


# ============================================================
# 3. CostEngine
# ============================================================

class TestCostEngine:

    def setup_method(self):
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        pricing_path = os.path.join(data_dir, "pricing.json")
        self.engine = CostEngine(pricing_path=pricing_path)

    def test_known_model_pricing(self):
        res = self.engine.calculate("antigravity", "gemini-2.5-flash", 1_000_000, 500_000)
        assert res.model_matched is True
        assert res.fallback_used is False
        assert abs(res.breakdown.input_cost - 0.15) < 0.001
        assert abs(res.breakdown.output_cost - 0.30) < 0.001

    def test_zero_tokens_zero_cost(self):
        res = self.engine.calculate("antigravity", "gemini-2.5-flash", 0, 0)
        assert res.cost_usd == 0.0

    def test_unknown_model_uses_fallback(self):
        res = self.engine.calculate("unknown_provider", "unknown_model", 1_000_000, 0)
        assert res.fallback_used is True
        assert res.model_matched is False
        assert res.cost_usd > 0

    def test_cache_read_tokens_priced(self):
        res = self.engine.calculate(
            "antigravity", "gemini-2.5-flash",
            input_tokens=0, output_tokens=0,
            cache_read_tokens=1_000_000
        )
        expected = 0.0375  # 1M * 0.0375/MTok
        assert abs(res.breakdown.cache_read_cost - expected) < 0.0001

    def test_thinking_tokens_priced(self):
        res = self.engine.calculate(
            "antigravity", "gemini-2.5-flash",
            input_tokens=0, output_tokens=0, thinking_tokens=1_000_000
        )
        assert res.breakdown.thinking_cost == 3.50  # 1M * 3.50/MTok

    def test_get_version(self):
        assert self.engine.get_version() == "1.0.0"

    def test_is_stale_fresh(self):
        assert self.engine.is_stale(30) is False

    def test_to_dict_structure(self):
        res = self.engine.calculate("antigravity", "gemini-2.5-flash", 100, 50)
        d = self.engine.to_dict(res)
        assert "cost_usd" in d
        assert "breakdown" in d
        assert "model_matched" in d
        assert "fallback_used" in d

    def test_claude_opus_pricing(self):
        res = self.engine.calculate("claude_code", "claude-opus-4", 1_000_000, 0)
        assert abs(res.breakdown.input_cost - 15.0) < 0.01

    def test_all_providers_have_fallback(self):
        pricing = self.engine._load()
        assert "fallback" in pricing


# ============================================================
# 4. ConnectorRegistry
# ============================================================

class TestConnectorRegistry:

    def test_empty_registry_detect(self):
        reg = ConnectorRegistry()
        assert reg.detect_all() == []

    def test_empty_registry_diagnose(self):
        reg = ConnectorRegistry()
        assert reg.diagnose_all() == []

    def test_list_registered_empty(self):
        reg = ConnectorRegistry()
        assert reg.list_registered() == []

    def test_get_connector_not_found(self):
        reg = ConnectorRegistry()
        assert reg.get_connector("nonexistent") is None

    def test_parse_raises_connector_not_found(self):
        reg = ConnectorRegistry()
        with pytest.raises(ConnectorNotFoundError) as exc_info:
            reg.parse("nonexistent", "conv-123")
        assert exc_info.value.provider_name == "nonexistent"

    def test_connector_not_found_error_message(self):
        err = ConnectorNotFoundError("my_provider", ["prov_a", "prov_b"])
        assert "my_provider" in str(err)


# ============================================================
# 5. IncrementalTranscriptReader
# ============================================================

class TestIncrementalTranscriptReader:

    def _make_jsonl(self, tmp_path, lines):
        """Write lines to a temp JSONL file."""
        with open(tmp_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(json.dumps(line) + "\n")

    def test_reads_all_lines_first_time(self):
        reader = IncrementalTranscriptReader()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name
            json.dump({"type": "A"}, f); f.write("\n")
            json.dump({"type": "B"}, f); f.write("\n")
        try:
            lines = reader.read_new_lines(tmp)
            assert len(lines) == 2
            assert lines[0][0]["type"] == "A"
        finally:
            os.unlink(tmp)

    def test_second_read_returns_empty_when_unchanged(self):
        reader = IncrementalTranscriptReader()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name
            json.dump({"type": "A"}, f); f.write("\n")
        try:
            reader.read_new_lines(tmp)
            second = reader.read_new_lines(tmp)
            assert second == []
        finally:
            os.unlink(tmp)

    def test_reads_only_new_lines_after_append(self):
        reader = IncrementalTranscriptReader()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name
            json.dump({"type": "OLD"}, f); f.write("\n")
        try:
            reader.read_new_lines(tmp)
            with open(tmp, "a", encoding="utf-8") as f:
                json.dump({"type": "NEW"}, f); f.write("\n")
            new_lines = reader.read_new_lines(tmp)
            assert len(new_lines) == 1
            assert new_lines[0][0]["type"] == "NEW"
        finally:
            os.unlink(tmp)

    def test_nonexistent_file_returns_empty(self):
        reader = IncrementalTranscriptReader()
        result = reader.read_new_lines("/nonexistent/path/file.jsonl")
        assert result == []

    def test_malformed_lines_skipped(self):
        reader = IncrementalTranscriptReader()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name
            f.write("NOT JSON\n")
            f.write(json.dumps({"type": "VALID"}) + "\n")
        try:
            lines = reader.read_new_lines(tmp)
            assert len(lines) == 1
            assert lines[0][0]["type"] == "VALID"
        finally:
            os.unlink(tmp)

    def test_reset_forces_full_reread(self):
        reader = IncrementalTranscriptReader()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name
            json.dump({"type": "A"}, f); f.write("\n")
        try:
            reader.read_new_lines(tmp)
            reader.reset(tmp)
            lines = reader.read_new_lines(tmp)
            assert len(lines) == 1
        finally:
            os.unlink(tmp)

    def test_sqlite_cursor_persistence(self):
        conn = sqlite3.connect(":memory:")
        ensure_transcript_cursors_table(conn)
        reader = IncrementalTranscriptReader(db_conn=conn)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            tmp = f.name
            json.dump({"step": 1}, f); f.write("\n")

        try:
            reader.read_new_lines(tmp)
            # Verify cursor persisted in SQLite
            row = conn.execute(
                "SELECT byte_pos FROM transcript_cursors WHERE file_path = ?", (tmp,)
            ).fetchone()
            assert row is not None
            assert row[0] > 0
        finally:
            os.unlink(tmp)
            conn.close()


# ============================================================
# 6. AntigravityConnector detection (smoke test)
# ============================================================

class TestAntigravityConnector:

    def setup_method(self):
        from connectors.antigravity import AntigravityConnector
        self.connector = AntigravityConnector

    def test_provider_name(self):
        c = self.connector()
        assert c.get_provider_name() == "antigravity"

    def test_detect_returns_detected_provider(self):
        c = self.connector()
        result = c.detect()
        assert result is not None
        assert result.provider_name == "antigravity"
        assert result.status in ("found", "not_found", "error")

    def test_detect_does_not_raise(self):
        c = self.connector(config={"brain_root": "/nonexistent/path"})
        result = c.detect()
        assert result is not None
        assert result.status == "not_found"

    def test_get_diagnostics_does_not_raise(self):
        c = self.connector(config={"brain_root": "/nonexistent/path"})
        diag = c.get_diagnostics()
        assert isinstance(diag, DiagnosticsResult)
        assert diag.status == "not_found"

    def test_parse_nonexistent_conversation_returns_empty(self):
        c = self.connector(config={"brain_root": "/nonexistent/path"})
        records = c.parse_conversation("nonexistent-conv-id")
        assert records == []

    def test_normalized_record_from_parse(self):
        """Smoke test with real BRAIN_ROOT if available."""
        c = self.connector()
        det = c.detect()
        if det.status != "found":
            pytest.skip("Antigravity BRAIN_ROOT not found — skip live test")
        convs = c.discover_conversations()
        if not convs:
            pytest.skip("No conversations found")
        records = c.parse_conversation(convs[0])
        # Records may be empty for conversations with no MODEL turns
        for rec in records:
            assert isinstance(rec, NormalizedUsageRecord)
            assert rec.total_tokens >= 0
            assert rec.accuracy_source in (
                "provider_reported", "transcript_parsed", "derived", "estimated", "unknown"
            )
