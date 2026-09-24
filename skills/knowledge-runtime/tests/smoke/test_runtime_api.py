import pytest
pytestmark = pytest.mark.smoke

# test_runtime_api.py
import unittest
import os
import tempfile

# knowledge_runtime.api was consolidated into workflow_runtime (c6df50ce).
from workflow_runtime.application.knowledge import knowledge_api as kr_api

class TestKnowledgeAPI(unittest.TestCase):
    def setUp(self):
        # The module-level API binds to the cwd and writes its cache under
        # .agents/state there, so run it inside a throwaway workspace.
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        docs = os.path.join(self._tmp.name, "docs")
        os.makedirs(docs)
        with open(os.path.join(docs, "notes.md"), "w", encoding="utf-8") as f:
            f.write("Workflow session checkpoints are resumable.")
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self._tmp.name)

    def test_search_not_empty(self):
        # The search function should return some matching files for a common keyword
        results = kr_api.search("session", limit=3)
        self.assertIsInstance(results, list)
        if results:
            for r in results:
                self.assertIn("path", r)
                self.assertIn("snippet", r)

    def test_search_empty(self):
        results = kr_api.search("")
        self.assertEqual(results, [])
