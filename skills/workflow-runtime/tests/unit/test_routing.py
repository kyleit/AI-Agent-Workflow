# test_routing.py
import pytest
pytestmark = pytest.mark.unit

import unittest
import os
import sys
import json
import shutil

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from agent_routing import load_agents, load_routing_table, validate_routing

class TestAgentRouting(unittest.TestCase):
    def setUp(self):
        # Resolve paths relative to the workspace root (4 levels up from tests/)
        _tests_dir = os.path.dirname(os.path.abspath(__file__))
        _workspace_root = os.path.abspath(os.path.join(_tests_dir, "..", "..", "..", ".."))
        self.manifest_path = os.path.join(_workspace_root, ".agents", "MANIFEST.json")
        self.agents_dir = os.path.join(_workspace_root, ".agents", "agents")
        
    def test_routing_resolution(self):
        table = load_routing_table(self.manifest_path)
        self.assertTrue(len(table) > 0)
        
        # Verify specific owner resolutions
        self.assertEqual(table["brainstorming"]["owner_agent"], "planner")
        self.assertEqual(table["brainstorming-to-plan"]["owner_agent"], "planner")
        self.assertEqual(table["plan-to-blueprint"]["owner_agent"], "architect")
        self.assertEqual(table["blueprint-to-implementation"]["owner_agent"], "coder")
        self.assertEqual(table["implementation-to-debug"]["owner_agent"], "reviewer")
        self.assertEqual(table["implementation-to-release"]["owner_agent"], "release-manager")
        
    def test_specialist_never_replaces_owner(self):
        table = load_routing_table(self.manifest_path)
        for skill_name, info in table.items():
            owner = info["owner_agent"]
            specs = info["specialist_agents"]
            self.assertNotIn(owner, specs)
            
    def test_agents_exist(self):
        agents = load_agents(self.agents_dir)
        self.assertIn("planner", agents)
        self.assertIn("architect", agents)
        self.assertIn("coder", agents)
        self.assertIn("reviewer", agents)
        self.assertIn("release-manager", agents)
        
    def test_validation_passes_on_current_framework(self):
        errors = validate_routing(self.manifest_path, self.agents_dir)
        self.assertEqual(errors, [], f"Validation errors found: {errors}")
        
    def test_invalid_routing_detection(self):
        # Create a temp manifest to test validation error detection
        temp_manifest = "MANIFEST_temp_test.json"
        temp_agents_dir = "agents_temp_test"
        
        if os.path.exists(temp_agents_dir):
            shutil.rmtree(temp_agents_dir)
        os.makedirs(temp_agents_dir, exist_ok=True)
        
        try:
            # 1. Test missing owner validation
            mock_manifest_data = {
                "skills": [
                    {
                        "name": "orphan-skill",
                        "command": "orphan",
                        "specialist_agents": []
                    }
                ]
            }
            with open(temp_manifest, "w", encoding="utf-8") as f:
                json.dump(mock_manifest_data, f)
                
            errors = validate_routing(temp_manifest, temp_agents_dir)
            self.assertTrue(any("does not have an owner_agent" in e for e in errors))
            
            # 2. Test cyclic handoff validation
            # Create two agents with mutual handoff targets
            with open(os.path.join(temp_agents_dir, "agent_a.md"), "w", encoding="utf-8") as f:
                f.write("---\nname: agent_a\nhandoff_target: agent_b\n---\n")
            with open(os.path.join(temp_agents_dir, "agent_b.md"), "w", encoding="utf-8") as f:
                f.write("---\nname: agent_b\nhandoff_target: agent_a\n---\n")
                
            mock_manifest_data_cycle = {
                "skills": [
                    {
                        "name": "cycle-skill-1",
                        "owner_agent": "agent_a"
                    },
                    {
                        "name": "cycle-skill-2",
                        "owner_agent": "agent_b"
                    }
                ]
            }
            with open(temp_manifest, "w", encoding="utf-8") as f:
                json.dump(mock_manifest_data_cycle, f)
                
            errors = validate_routing(temp_manifest, temp_agents_dir)
            self.assertTrue(any("Cyclic agent handoff detected" in e for e in errors))
            
        finally:
            if os.path.exists(temp_manifest):
                os.remove(temp_manifest)
            if os.path.exists(temp_agents_dir):
                shutil.rmtree(temp_agents_dir)

if __name__ == "__main__":
    unittest.main()
