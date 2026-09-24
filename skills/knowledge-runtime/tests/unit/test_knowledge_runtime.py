import pytest
pytestmark = pytest.mark.unit

import os
import unittest
import shutil
import tempfile

# knowledge_runtime was consolidated into workflow_runtime (c6df50ce).
from workflow_runtime.application.knowledge.knowledge_api import KnowledgeAPI, search, read, save, sync
from workflow_runtime.application.knowledge.cache_manager import CacheManager

_RETIRED_INDEX = ("retired in c6df50ce: knowledge_runtime/index.py and analyzer.py "
                  "(KnowledgeIndexer, QualityAnalyzer) were removed with no successor")

class TestKnowledgeRuntime(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = "test_memory.config.json"
        
        # Write dummy config
        with open(os.path.join(self.test_dir, self.config_path), "w", encoding="utf-8") as f:
            f.write('{"active_provider": "markdown", "cache_enabled": true}')

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_api_scaffolding_and_save_read(self):
        api = KnowledgeAPI(config_path=self.config_path, workspace_root=self.test_dir)
        
        # Test saving markdown file
        save_status = api.save("docs/test_note.md", "# Test Note\nThis is [[Target Note]].")
        self.assertTrue(save_status)
        
        # Test reading markdown file
        content = api.read("docs/test_note.md")
        self.assertIn("# Test Note", content)

    def test_cache_manager(self):
        cache_file = "state/knowledge_cache.json"
        manager = CacheManager(cache_file=cache_file, ttl=10, workspace_root=self.test_dir)
        
        # Initial Cache get should be None
        self.assertIsNone(manager.get("query_string", 5))
        
        # Set cache
        dummy_results = [{"path": "docs/test.md", "snippet": "matched text", "score": 1.0}]
        manager.set("query_string", 5, dummy_results)
        
        # Get cache (hit)
        cached_results = manager.get("query_string", 5)
        self.assertEqual(cached_results, dummy_results)

    @unittest.skip(_RETIRED_INDEX)
    def test_indexer_backlinks(self):
        indexer = KnowledgeIndexer()
        text = "This is a note linking to [[First Note]] and [[Second Note]]."
        links = indexer.extract_backlinks(text)
        self.assertEqual(links, ["First Note", "Second Note"])

    @unittest.skip(_RETIRED_INDEX)
    def test_quality_analyzer_orphans(self):
        indexer = KnowledgeIndexer()
        analyzer = QualityAnalyzer(indexer)
        
        docs_map = {
            "docs/note_a.md": "Link to [[Note_B]]",
            "docs/note_b.md": "No links here"
        }
        
        orphans = analyzer.find_orphan_notes(docs_map)
        self.assertIn("docs/note_a.md", orphans)
        self.assertNotIn("docs/note_b.md", orphans)

    def test_public_exports(self):
        # Verify functions are callable and correctly exported
        self.assertTrue(callable(search))
        self.assertTrue(callable(read))
        self.assertTrue(callable(save))
        self.assertTrue(callable(sync))
        
        # Test basic calling scaffolding
        res = sync(provider="unsupported")
        self.assertEqual(res["status"], "failure")

if __name__ == "__main__":
    unittest.main()
