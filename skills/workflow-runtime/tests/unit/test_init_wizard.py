# test_init_wizard.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import os
import sys
import json
import shutil
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from init_wizard import RecommendationEngine, ScaffoldPlanner

class TestInitWizard(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_recommendation_engine(self):
        answers_go = {"primary_language": "Go"}
        recs_go = RecommendationEngine.get_recommendations(answers_go)
        self.assertEqual(recs_go["backend_framework"], "Fiber")
        self.assertEqual(recs_go["database"], "PostgreSQL")

        answers_py = {"primary_language": "Python"}
        recs_py = RecommendationEngine.get_recommendations(answers_py)
        self.assertEqual(recs_py["backend_framework"], "FastAPI")
        self.assertEqual(recs_py["database"], "PostgreSQL")

    def test_scaffold_planner_generation(self):
        planner = ScaffoldPlanner(self.test_dir)
        config = {
            "schema_version": "1.0.0",
            "project": {
                "name": "my-test-proj",
                "display_name": "My Test Project",
                "description": "Just testing scaffold generation"
            },
            "languages": ["Python"],
            "database": {
                "engine": "SQLite"
            },
            "git": {
                "initialize": False
            }
        }
        res = planner.generate_scaffold(config)
        self.assertTrue(res)

        # Verify folders and files
        config_path = os.path.join(self.test_dir, ".agents", "project.config.json")
        self.assertTrue(os.path.exists(config_path))
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["project"]["name"], "my-test-proj")

        profile_path = os.path.join(self.test_dir, ".agents", "PROJECT_PROFILE.md")
        self.assertTrue(os.path.exists(profile_path))

        docs_dir = os.path.join(self.test_dir, "docs", "brainstorming")
        self.assertTrue(os.path.exists(docs_dir))

if __name__ == "__main__":
    unittest.main()
