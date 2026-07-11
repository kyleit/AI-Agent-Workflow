# global_knowledge_graph.py
class GlobalKnowledgeGraph:
    """
    FEAT-106: Global Knowledge Graph
    Maps cross-project modules and dependencies relationships.
    """
    def __init__(self):
        self.graph = {}

    def add_relationship(self, entity_a: str, entity_b: str, rel_type: str) -> None:
        if entity_a not in self.graph:
            self.graph[entity_a] = []
        self.graph[entity_a].append((entity_b, rel_type))
