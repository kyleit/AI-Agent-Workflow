# test_breakdown.py
import unittest
import os
import sys
import json
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from breakdown_engine import generate_breakdown, update_breakdown_file

class TestContextBreakdown(unittest.TestCase):
    def setUp(self):
        self.workspace_dir = os.path.join(os.path.dirname(__file__), "temp_test_workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Create doc folders
        os.makedirs(os.path.join(self.workspace_dir, "docs", "brainstorming"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, "docs", "plans"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, "docs", "designs"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, "docs", "adr"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, ".agents", "memory"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, ".agents", "state"), exist_ok=True)
        
        # Write dummy files to simulate doc sizes
        with open(os.path.join(self.workspace_dir, "AI_RULES.md"), "w", encoding="utf-8") as f:
            f.write("# Rules\n" * 100) # ~ 800 chars
            
        with open(os.path.join(self.workspace_dir, ".agents", "AGENTS.md"), "w", encoding="utf-8") as f:
            f.write("# Agents\n" * 50) # ~ 400 chars
            
        with open(os.path.join(self.workspace_dir, "docs", "plans", "FEAT-032_plan.md"), "w", encoding="utf-8") as f:
            f.write("# Plan\n" * 150) # ~ 1200 chars

    def tearDown(self):
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)

    def test_context_classification(self):
        session_data = {
            "conversation_id": "test_conv_123",
            "current_skill": "initialize-workflow",
            "current_command": "init"
        }
        
        bd = generate_breakdown(session_data, self.workspace_dir)
        self.assertEqual(bd["conversation_id"], "test_conv_123")
        self.assertGreater(bd["total_tokens"], 0)
        
        # Find category breakdown
        categories = {item["category"]: item for item in bd["breakdown"]}
        
        self.assertIn("AI_RULES", categories)
        self.assertIn("AGENTS", categories)
        self.assertIn("Plans", categories)
        
        self.assertGreater(categories["AI_RULES"]["tokens"], 0)
        self.assertGreater(categories["AGENTS"]["tokens"], 0)
        self.assertGreater(categories["Plans"]["tokens"], 0)
        
        # Check details presence
        self.assertGreater(len(categories["AI_RULES"]["details"]), 0)
        self.assertEqual(categories["AI_RULES"]["details"][0]["name"], "AI_RULES.md")

    def test_percentages_total_100(self):
        session_data = {
            "conversation_id": "test_conv_123",
            "current_skill": "initialize-workflow",
            "current_command": "init"
        }
        
        bd = generate_breakdown(session_data, self.workspace_dir)
        total_pct = sum(item["percentage"] for item in bd["breakdown"])
        
        # Total percentage should sum to approximately 100%
        self.assertAlmostEqual(total_pct, 100.0, places=1)

if __name__ == "__main__":
    unittest.main()
