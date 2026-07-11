import pytest
pytestmark = pytest.mark.unit

# test_cache.py
import unittest
import sys
import os
import time

# Add knowledge-runtime/scripts paths dynamically
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from cache import RuntimeCache

class TestRuntimeCache(unittest.TestCase):
    def test_cache_set_and_get(self):
        cache = RuntimeCache(db_path=".agents/state/test_knowledge_cache.json", ttl_seconds=1)
        cache.clear()
        
        # Set cache
        cache.set("query_key", {"data": "test_value"})
        
        # Get cache instantly (should hit)
        val = cache.get("query_key")
        self.assertEqual(val, {"data": "test_value"})
        
        # Wait for TTL expiration (1 second)
        time.sleep(1.1)
        
        # Get cache again (should miss due to expiration)
        val_expired = cache.get("query_key")
        self.assertIsNone(val_expired)
        
        # Clean up
        cache.clear()
        if os.path.exists(".agents/state/test_knowledge_cache.json"):
            try:
                os.remove(".agents/state/test_knowledge_cache.json")
            except Exception:
                pass
PrePreProced = True
