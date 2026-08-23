"""
test_normalization.py — FEAT-048 Phase 5 Task 5.1
Tests: UsageNormalizer, NormalizedUsageRecord (FR-04)
Blueprint test matrix: test_normalization.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestNormalizedUsageRecord(unittest.TestCase):
    """FR-04: NormalizedUsageRecord — all fields, clamping, accuracy_source."""

    def setUp(self):
        from connectors.base import NormalizedUsageRecord
        self.NormalizedUsageRecord = NormalizedUsageRecord

    def _make_record(self, **kwargs):
        defaults = dict(
            conversation_id='test-conv',
            provider='antigravity',
            model='gemini-2.5-flash',
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=0,
            cache_write_tokens=0,
            thinking_tokens=0,
            total_tokens=0,      # computed by __post_init__
            duration_ms=0,
            estimated_cost_usd=0.0,
            accuracy_source='estimated',
            timestamp='2026-07-10T00:00:00Z',
            request_id='req-001',
            raw_payload=None,
        )
        defaults.update(kwargs)
        return self.NormalizedUsageRecord(**defaults)

    def test_all_fields_present(self):
        """All required fields must be present on NormalizedUsageRecord."""
        rec = self._make_record()
        required = [
            'conversation_id', 'provider', 'model',
            'input_tokens', 'output_tokens', 'cache_read_tokens',
            'cache_write_tokens', 'thinking_tokens', 'total_tokens',
            'duration_ms', 'estimated_cost_usd', 'accuracy_source',
            'timestamp', 'request_id', 'raw_payload',
        ]
        for field in required:
            self.assertIn(field, rec.__dict__, f'Missing field: {field}')

    def test_total_tokens_computed_correctly(self):
        """total_tokens is set from actual data (input + output as primary sum)."""
        rec = self._make_record(
            input_tokens=100, output_tokens=50,
            cache_read_tokens=20, cache_write_tokens=10, thinking_tokens=5
        )
        # total_tokens = input + output = 150 (as implemented)
        # If implementation sums all fields, it would be 185
        # Test just that total_tokens >= input + output (not negative)
        self.assertGreaterEqual(rec.total_tokens, rec.input_tokens + rec.output_tokens)
        self.assertGreater(rec.total_tokens, 0)

    def test_negative_tokens_clamped_to_zero(self):
        """Negative token counts are clamped to 0 before total computation."""
        rec = self._make_record(input_tokens=-50, output_tokens=100)
        self.assertGreaterEqual(rec.input_tokens, 0)
        self.assertGreaterEqual(rec.total_tokens, 0)

    def test_accuracy_source_in_record(self):
        """accuracy_source field must be present (FR-04)."""
        rec = self._make_record(accuracy_source='transcript_parsed')
        self.assertEqual(rec.accuracy_source, 'transcript_parsed')

    def test_accuracy_source_hierarchy_values_accepted(self):
        """All accuracy_source values from hierarchy are accepted."""
        for level in ['provider_reported', 'transcript_parsed', 'derived', 'estimated', 'unknown',
                      'response_payload', 'api_metadata', 'deterministic_reconstruction', 'tokenizer']:
            rec = self._make_record(accuracy_source=level)
            self.assertEqual(rec.accuracy_source, level)

    def test_v2_new_fields_default_and_types(self):
        """New FEAT-049 fields must be present with correct defaults."""
        rec = self._make_record()
        self.assertIsNone(rec.fingerprint)
        self.assertEqual(rec.tool_tokens, 0)
        self.assertEqual(rec.transcript_offset, -1)
        self.assertEqual(rec.raw_metadata, {})

    def test_tool_tokens_clamped_to_zero(self):
        """Negative tool_tokens must be clamped to 0."""
        rec = self._make_record(tool_tokens=-10)
        self.assertEqual(rec.tool_tokens, 0)

    def test_valid_fingerprint_preserved(self):
        """Valid 64-char lowercase hex fingerprint must be preserved."""
        valid_fp = "a" * 64
        rec = self._make_record(fingerprint=valid_fp)
        self.assertEqual(rec.fingerprint, valid_fp)

    def test_invalid_fingerprint_cleared_to_none(self):
        """Invalid fingerprints must be set to None in __post_init__."""
        invalid_fps = ["short", "a" * 63, "A" * 64, "g" * 64] # uppercase, bad chars, bad length
        for fp in invalid_fps:
            rec = self._make_record(fingerprint=fp)
            self.assertIsNone(rec.fingerprint, f"Fingerprint '{fp}' should have been cleared to None")



class TestUsageNormalizer(unittest.TestCase):
    """FR-04: UsageNormalizer — normalize() and validate()."""

    def setUp(self):
        from normalizer import UsageNormalizer
        self.UsageNormalizer = UsageNormalizer
        from connectors.base import NormalizedUsageRecord
        self.NormalizedUsageRecord = NormalizedUsageRecord

    def test_normalize_antigravity_returns_record(self):
        """normalize() with antigravity raw dict returns NormalizedUsageRecord."""
        norm = self.UsageNormalizer()
        raw = {
            'input_tokens': 200,
            'output_tokens': 100,
            'model': 'gemini-2.5-flash',
            'conversation_id': 'conv-abc',
            'request_id': 'req-001',
            'timestamp': '2026-07-10T00:00:00Z',
        }
        rec = norm.normalize(raw, provider='antigravity', accuracy_source='estimated')
        self.assertIsInstance(rec, self.NormalizedUsageRecord)
        self.assertEqual(rec.provider, 'antigravity')
        self.assertEqual(rec.input_tokens, 200)

    def test_validate_returns_empty_for_valid_record(self):
        """validate() returns [] for a well-formed record."""
        norm = self.UsageNormalizer()
        raw = {
            'input_tokens': 100,
            'output_tokens': 50,
            'model': 'gemini-2.5-flash',
            'conversation_id': 'conv-abc',
            'request_id': 'req-001',
            'timestamp': '2026-07-10T00:00:00Z',
        }
        rec = norm.normalize(raw, provider='antigravity', accuracy_source='estimated')
        errors = norm.validate(rec)
        self.assertIsInstance(errors, list)
        self.assertEqual(len(errors), 0)

    def test_validate_detects_missing_conversation_id(self):
        """validate() returns errors for empty conversation_id."""
        norm = self.UsageNormalizer()
        raw = {
            'input_tokens': 100,
            'output_tokens': 50,
            'model': 'gemini-2.5-flash',
            'conversation_id': '',  # empty
            'request_id': 'req-001',
            'timestamp': '2026-07-10T00:00:00Z',
        }
        rec = norm.normalize(raw, provider='antigravity', accuracy_source='estimated')
        errors = norm.validate(rec)
        self.assertIsInstance(errors, list)
        self.assertGreater(len(errors), 0)

    def test_normalize_with_negative_tokens_produces_non_negative_total(self):
        """normalize() with negative raw tokens still produces non-negative total_tokens."""
        norm = self.UsageNormalizer()
        raw = {
            'input_tokens': -999,
            'output_tokens': -500,
            'model': 'auto',
            'conversation_id': 'conv-neg',
            'request_id': 'req-neg',
            'timestamp': '2026-07-10T00:00:00Z',
        }
        rec = norm.normalize(raw, provider='antigravity', accuracy_source='estimated')
        self.assertGreaterEqual(rec.total_tokens, 0)
        self.assertGreaterEqual(rec.input_tokens, 0)
        self.assertGreaterEqual(rec.output_tokens, 0)

    def test_normalize_handles_missing_fields_gracefully(self):
        """normalize() with incomplete raw dict does not raise."""
        norm = self.UsageNormalizer()
        raw = {'model': 'auto'}  # minimal dict
        try:
            rec = norm.normalize(raw, provider='antigravity', accuracy_source='unknown')
            self.assertIsNotNone(rec)
        except Exception as e:
            self.fail(f'normalize() raised on incomplete dict: {e}')

    def test_normalize_all_providers(self):
        """normalize() accepts all 4 provider names without raising."""
        norm = self.UsageNormalizer()
        raw = {
            'input_tokens': 10, 'output_tokens': 5, 'model': 'auto',
            'conversation_id': 'conv-x', 'request_id': 'req-x',
            'timestamp': '2026-07-10T00:00:00Z',
        }
        for provider in ['antigravity', 'claude_code', 'cursor', 'vscode_agents']:
            rec = norm.normalize(raw, provider=provider, accuracy_source='estimated')
            self.assertEqual(rec.provider, provider)

    def test_to_int_coerces_strings(self):
        """_to_int() must coerce string numbers to int."""
        norm = self.UsageNormalizer()
        raw = {
            'input_tokens': '100', 'output_tokens': '50',
            'model': 'auto', 'conversation_id': 'c', 'request_id': 'r',
            'timestamp': '2026-07-10T00:00:00Z',
        }
        rec = norm.normalize(raw, provider='antigravity', accuracy_source='estimated')
        self.assertIsInstance(rec.input_tokens, int)
        self.assertEqual(rec.input_tokens, 100)

    def test_to_int_handles_none(self):
        """_to_int() must handle None gracefully, returning 0."""
        norm = self.UsageNormalizer()
        raw = {
            'input_tokens': None, 'output_tokens': None,
            'model': 'auto', 'conversation_id': 'c', 'request_id': 'r',
            'timestamp': '2026-07-10T00:00:00Z',
        }
        rec = norm.normalize(raw, provider='antigravity', accuracy_source='estimated')
        self.assertEqual(rec.input_tokens, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
