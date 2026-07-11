# File path: vir_runtime/planner/graph.py
from typing import Dict, List, Any, Set

class StateTransitionGraph:
    def __init__(self):
        self.nodes: Set[str] = set()
        self.edges: Dict[str, List[Dict[str, Any]]] = {}
        self.parent_map: Dict[str, Dict[str, Any]] = {} # Child -> Parent and action taken

    def add_node(self, state_hash: str) -> None:
        """Register layout state hash node."""
        self.nodes.add(state_hash)
        if state_hash not in self.edges:
            self.edges[state_hash] = []

    def add_edge(self, from_hash: str, to_hash: str, action: Dict[str, Any]) -> None:
        """Catalog edge transition action mappings."""
        self.add_node(from_hash)
        self.add_node(to_hash)
        self.edges[from_hash].append({
            "target": to_hash,
            "action": action
        })
        # Save parent map details to support backtrack path trace
        if to_hash not in self.parent_map:
            self.parent_map[to_hash] = {
                "parent": from_hash,
                "action": action
            }

    def get_backtrack_route(self, from_hash: str) -> List[Dict[str, Any]]:
        """Resolve shortest path actions sequence back to origin root node."""
        path = []
        curr = from_hash
        # Follow parent map paths back to start node (which has no parent)
        while curr in self.parent_map:
            step = self.parent_map[curr]
            # Backtrack means we want to undo/re-run from parent
            path.append(step["action"])
            curr = step["parent"]
        
        # Path trace goes backwards, reverse to obtain correct steps order
        path.reverse()
        return path
