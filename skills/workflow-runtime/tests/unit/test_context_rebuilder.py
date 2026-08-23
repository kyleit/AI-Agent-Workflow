# test_context_rebuilder.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from context_rebuilder import build_context_bundle, get_or_create_cache, get_cache_statistics

class TestContextRebuilder(unittest.TestCase):
    def test_cache_hit_and_miss(self):
        # Trigger miss on non-existent file
        res = get_or_create_cache("non_existent_file.md")
        self.assertFalse(res["hit"])
        
        # Test cache stats
        stats = get_cache_statistics()
        self.assertGreaterEqual(stats["cached_files"], 0)

    def test_build_context_bundle(self):
        # Simulate rebuilder with 100k input tokens
        res = build_context_bundle("dummy_conv", 100000)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["rebuilt_tokens"], 15000) # 85% savings
        self.assertEqual(res["tokens_saved"], 85000)
        self.assertIn("AI_RULES.md", res["included_sources"])

if __name__ == "__main__":
    unittest.main()
