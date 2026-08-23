# global_knowledge_graph.py
from __future__ import annotations


class GlobalKnowledgeGraph:
    """
    FEAT-106: Global Knowledge Graph
    Maps cross-project modules and dependencies relationships.
    """
    def __init__(self) -> None:
        self.graph: dict[str, list[tuple[str, str]]] = {}

    def add_relationship(self, entity_a: str, entity_b: str, rel_type: str) -> None:
        if entity_a not in self.graph:
            self.graph[entity_a] = []
        self.graph[entity_a].append((entity_b, rel_type))


__all__ = ["GlobalKnowledgeGraph"]
