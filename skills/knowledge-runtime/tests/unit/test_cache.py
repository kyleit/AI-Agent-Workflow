import pytest
pytestmark = pytest.mark.unit

# test_cache.py
import unittest
import tempfile
import time

# scripts/cache.py (RuntimeCache) was retired in a9d51716; its TTL cache role is
# served by the consolidated CacheManager.
from workflow_runtime.application.knowledge.cache_manager import CacheManager

class TestRuntimeCache(unittest.TestCase):
    def test_cache_set_and_get(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # expires_at is truncated to whole seconds, so a 1s TTL can expire
        # immediately; 2s guarantees at least 1s of validity.
        cache = CacheManager(cache_file="state/test_knowledge_cache.json", ttl=2, workspace_root=tmp.name)
        cache.invalidate_all()

        # Set cache
        cache.set("query_key", 5, [{"data": "test_value"}])

        # Get cache instantly (should hit)
        val = cache.get("query_key", 5)
        self.assertEqual(val, [{"data": "test_value"}])

        # Wait for TTL expiration
        time.sleep(2.1)

        # Get cache again (should miss due to expiration)
        val_expired = cache.get("query_key", 5)
        self.assertIsNone(val_expired)
