# test_catalog.py
import unittest
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))

from agent_routing import load_agents

class TestAgentCatalog(unittest.TestCase):
    def setUp(self):
        self.agents_dir = "agents"
        
    def test_catalog_size_and_attributes(self):
        agents = load_agents(self.agents_dir)
        # Should contain 5 core agents + 35 specialists = 40 agents total (or more)
        self.assertTrue(len(agents) >= 40, f"Expected at least 40 agents, got {len(agents)}")
        
        required_attributes = [
            "name", "role", "responsibilities", "artifact_ownership", "allowed_reads",
            "allowed_writes", "forbidden_actions", "input_contract", "output_contract",
            "handoff_target", "done_criteria", "can_run_in_parallel", "agent_category",
            "phase", "required_skills", "required_memory", "required_rag_context",
            "runtime_requirements"
        ]
        
        for name, meta in agents.items():
            for attr in required_attributes:
                self.assertIn(attr, meta, f"Agent '{name}' is missing required attribute '{attr}'")

if __name__ == "__main__":
    unittest.main()
