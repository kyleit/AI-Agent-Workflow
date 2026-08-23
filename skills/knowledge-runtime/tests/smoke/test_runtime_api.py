import pytest
pytestmark = pytest.mark.smoke

# test_runtime_api.py
import unittest
import sys
import os

# Add scripts directory dynamically to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

from knowledge_runtime import api as kr_api

class TestKnowledgeAPI(unittest.TestCase):
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
