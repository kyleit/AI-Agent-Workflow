import pytest
pytestmark = pytest.mark.unit

# test_qmd.py
import unittest
import sys
import os

# Add workflow-runtime/scripts and knowledge-runtime/scripts paths dynamically
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "workflow-runtime", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts")))

import db

class TestQmdDatabase(unittest.TestCase):
    def test_save_and_get_qmd_metadata(self):
        # Clear existing
        db.clear_qmd_metadata(project_id="test_proj")
        
        # Save a mock record
        record = {
            "point_id": "test_point_123",
            "project_id": "test_proj",
            "module": "test_mod",
            "feature_id": "FEAT-999",
            "file_path": "docs/test_file.md",
            "section_heading": "Test Heading",
            "content_hash": "abc123hash"
        }
        db.save_qmd_metadata(record)
        
        # Query it back
        results = db.get_qmd_metadata({"project_id": "test_proj", "module": "test_mod"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["point_id"], "test_point_123")
        self.assertEqual(results[0]["section_heading"], "Test Heading")
        self.assertEqual(results[0]["content_hash"], "abc123hash")
        
        # Clean up
        db.clear_qmd_metadata(project_id="test_proj")
        results_post = db.get_qmd_metadata({"project_id": "test_proj"})
        self.assertEqual(len(results_post), 0)
