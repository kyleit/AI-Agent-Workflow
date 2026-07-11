import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
from global_knowledge_graph import GlobalKnowledgeGraph

def test_knowledge_graph():
    kg = GlobalKnowledgeGraph()
    kg.add_relationship("moduleA", "moduleB", "DEPENDS_ON")
    assert len(kg.graph["moduleA"]) == 1
