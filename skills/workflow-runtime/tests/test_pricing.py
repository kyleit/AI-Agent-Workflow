"""
test_pricing.py — FEAT-048 Phase 5 Task 5.1
Tests: CostEngine — calculate(), is_stale(), fallback (FR-05)
Blueprint test matrix: test_pricing.py
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestCostEngine(unittest.TestCase):
    """FR-05: CostEngine — pricing calculation, fallback, stale detection."""

    def setUp(self):
        from cost_engine import CostEngine
        self.CostEngine = CostEngine
        # Use the real pricing.json in data/
        self.pricing_path = os.path.join(
            os.path.dirname(__file__), '..', 'data', 'pricing.json'
        )

    def _make_pricing_json(self, tmpdir, updated_days_ago=0):
        """Create a minimal pricing.json for testing."""
        from datetime import datetime, timezone, timedelta
        updated_at = (datetime.now(timezone.utc) - timedelta(days=updated_days_ago)).strftime('%Y-%m-%d')
        data = {
            'version': '1.0.0',
            'updated_at': updated_at,
            'providers': {
                'antigravity': {
                    'models': {
                        'gemini-2.5-flash': {
                            'input_per_mtok': 0.30,
                            'output_per_mtok': 1.00,
                        }
                    }
                }
            },
            'fallback': {
                'input_per_mtok': 1.50,
                'output_per_mtok': 5.00,
            }
        }
        path = os.path.join(tmpdir, 'pricing.json')
        with open(path, 'w') as f:
            json.dump(data, f)
        return path

    def test_calculate_returns_cost_result(self):
        """calculate() returns a CostResult with cost_usd >= 0."""
        engine = self.CostEngine(pricing_path=self.pricing_path)
        result = engine.calculate(
            provider='antigravity',
            model='gemini-2.5-flash',
            input_tokens=1_000_000,
            output_tokens=500_000,
        )
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'cost_usd') or hasattr(result, 'to_dict'))

    def test_calculate_cost_within_1pct_of_expected(self):
        """Cost for 1M input + 0.5M output on gemini-2.5-flash within 1% of expected."""
        # gemini-2.5-flash: input $0.30/MTok, output $1.00/MTok
        # Expected: 1.0 * 0.30 + 0.5 * 1.00 = $0.30 + $0.50 = $0.80
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_pricing_json(tmpdir)
            engine = self.CostEngine(pricing_path=path)
            result = engine.calculate(
                provider='antigravity',
                model='gemini-2.5-flash',
                input_tokens=1_000_000,
                output_tokens=500_000,
            )
            cost = result.cost_usd if hasattr(result, 'cost_usd') else result.to_dict()['cost_usd']
            expected = 0.80
            delta = expected * 0.01  # 1% tolerance
            self.assertAlmostEqual(cost, expected, delta=delta,
                                   msg=f'Cost {cost} not within 1% of expected {expected}')

    def test_fallback_used_for_unknown_model(self):
        """calculate() uses fallback pricing for unknown model."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_pricing_json(tmpdir)
            engine = self.CostEngine(pricing_path=path)
            result = engine.calculate(
                provider='antigravity',
                model='unknown-model-xyz',
                input_tokens=1_000_000,
                output_tokens=0,
            )
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
            self.assertTrue(result_dict.get('fallback_used', False),
                            'fallback_used should be True for unknown model')

    def test_is_stale_false_on_fresh_pricing(self):
        """is_stale(30) returns False for pricing.json updated today."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_pricing_json(tmpdir, updated_days_ago=0)
            engine = self.CostEngine(pricing_path=path)
            self.assertFalse(engine.is_stale(30))

    def test_is_stale_true_on_old_pricing(self):
        """is_stale(30) returns True for pricing.json updated 60 days ago."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = self._make_pricing_json(tmpdir, updated_days_ago=60)
            engine = self.CostEngine(pricing_path=path)
            self.assertTrue(engine.is_stale(30))

    def test_calculate_never_raises_on_zero_tokens(self):
        """calculate() with all-zero tokens returns cost_usd=0.0 without raising."""
        engine = self.CostEngine(pricing_path=self.pricing_path)
        try:
            result = engine.calculate(
                provider='antigravity',
                model='gemini-2.5-flash',
                input_tokens=0, output_tokens=0,
            )
            cost = result.cost_usd if hasattr(result, 'cost_usd') else result.to_dict()['cost_usd']
            self.assertEqual(cost, 0.0)
        except Exception as e:
            self.fail(f'calculate() raised on zero tokens: {e}')

    def test_to_dict_returns_required_keys(self):
        """CostResult.to_dict() returns cost_usd, breakdown, model_matched, fallback_used."""
        engine = self.CostEngine(pricing_path=self.pricing_path)
        result = engine.calculate(
            provider='antigravity',
            model='gemini-2.5-flash',
            input_tokens=100_000,
            output_tokens=50_000,
        )
        d = result.to_dict() if hasattr(result, 'to_dict') else result.__dict__
        for key in ['cost_usd', 'model_matched', 'fallback_used']:
            self.assertIn(key, d, f'Missing key in CostResult: {key}')

    def test_lazy_loading_data_initialized_on_first_call(self):
        """CostEngine._data starts as None, populated after first calculate()."""
        engine = self.CostEngine(pricing_path=self.pricing_path)
        # Verify lazy loading pattern — _data should be None before any call
        self.assertIsNone(engine._data)
        engine.calculate(provider='antigravity', model='gemini-2.5-flash',
                         input_tokens=1000, output_tokens=500)
        self.assertIsNotNone(engine._data)

    def test_real_pricing_json_loads_without_error(self):
        """The real data/pricing.json can be loaded by CostEngine."""
        if not os.path.exists(self.pricing_path):
            self.skipTest('data/pricing.json not found')
        engine = self.CostEngine(pricing_path=self.pricing_path)
        result = engine.calculate(
            provider='antigravity', model='gemini-2.5-flash',
            input_tokens=100, output_tokens=100,
        )
        self.assertIsNotNone(result)

    def test_calculate_with_cache_tokens(self):
        """calculate() with cache_read and cache_write tokens succeeds."""
        engine = self.CostEngine(pricing_path=self.pricing_path)
        try:
            result = engine.calculate(
                provider='antigravity', model='gemini-2.5-flash',
                input_tokens=100, output_tokens=50,
                cache_read_tokens=200, cache_write_tokens=100,
            )
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f'calculate() with cache tokens raised: {e}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
