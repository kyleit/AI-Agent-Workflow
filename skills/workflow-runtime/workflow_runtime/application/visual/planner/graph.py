# File path: vir_runtime/planner/graph.py
from __future__ import annotations

from typing import Any


class StateTransitionGraph:
    def __init__(self) -> None:
        self.nodes: set[str] = set()
        self.edges: dict[str, list[dict[str, Any]]] = {}
        self.parent_map: dict[str, dict[str, Any]] = {}

    def add_node(self, state_hash: str) -> None:
        """Register layout state hash node."""
        self.nodes.add(state_hash)
        if state_hash not in self.edges:
            self.edges[state_hash] = []

    def add_edge(self, from_hash: str, to_hash: str, action: dict[str, Any]) -> None:
        """Catalog edge transition action mappings."""
        self.add_node(from_hash)
        self.add_node(to_hash)
        self.edges[from_hash].append({
            "target": to_hash,
            "action": action
        })
        if to_hash not in self.parent_map:
            self.parent_map[to_hash] = {
                "parent": from_hash,
                "action": action
            }

    def get_backtrack_route(self, from_hash: str) -> list[dict[str, Any]]:
        """Resolve shortest path actions sequence back to origin root node."""
        path: list[dict[str, Any]] = []
        curr = from_hash
        while curr in self.parent_map:
            step = self.parent_map[curr]
            path.append(step["action"])
            curr = step["parent"]

        path.reverse()
        return path


__all__ = ["StateTransitionGraph"]
