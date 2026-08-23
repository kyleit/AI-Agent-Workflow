# test_docs_artifact_placement.py
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
from validator import validate_artifact_placement

class TestDocsArtifactPlacement(unittest.TestCase):
    def test_brainstorming_docs_placement(self):
        self.assertTrue(validate_artifact_placement("docs/brainstorming/FEAT-404.md", "brainstorming"))
        self.assertFalse(validate_artifact_placement("docs/plans/FEAT-404_plan.md", "brainstorming"))
        
    def test_planning_docs_placement(self):
        self.assertTrue(validate_artifact_placement("docs/plans/FEAT-404_plan.md", "planning"))
        self.assertFalse(validate_artifact_placement("docs/blueprints/FEAT-404_blueprint.md", "planning"))
        
    def test_blueprint_docs_placement(self):
        self.assertTrue(validate_artifact_placement("docs/blueprints/FEAT-404_blueprint.md", "blueprint"))
        self.assertFalse(validate_artifact_placement("docs/plans/FEAT-404_plan.md", "blueprint"))

if __name__ == "__main__":
    unittest.main()
