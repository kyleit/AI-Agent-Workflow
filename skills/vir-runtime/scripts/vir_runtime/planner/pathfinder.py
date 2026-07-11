# File path: vir_runtime/planner/pathfinder.py
from collections import deque
from typing import List, Dict, Any, Set, Optional
from vir_runtime.planner.graph import StateTransitionGraph

class GoalUnreachableError(Exception):
    pass

class Pathfinder:
    def __init__(self, graph: StateTransitionGraph):
        self.graph = graph

    def find_shortest_path(self, start_hash: str, target_hash: str) -> List[Dict[str, Any]]:
        """Run A*/BFS search algorithms to identify optimal click sequence paths."""
        if start_hash not in self.graph.nodes or target_hash not in self.graph.nodes:
            raise GoalUnreachableError(f"Start node '{start_hash}' or target node '{target_hash}' not registered in graph.")

        # Using BFS (a specific case of A* with uniform costs) to find shortest path
        queue = deque([[start_hash]])
        visited: Set[str] = {start_hash}
        
        # Track path actions
        action_paths: Dict[str, List[Dict[str, Any]]] = {start_hash: []}

        while queue:
            path = queue.popleft()
            node = path[-1]

            if node == target_hash:
                return action_paths[node]

            for edge in self.graph.edges.get(node, []):
                neighbor = edge["target"]
                action = edge["action"]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    # Copy parent path steps and append current action
                    action_paths[neighbor] = action_paths[node] + [action]
                    new_path = list(path) + [neighbor]
                    queue.append(new_path)

        raise GoalUnreachableError(f"Target node '{target_hash}' is unreachable from start node '{start_hash}'.")
