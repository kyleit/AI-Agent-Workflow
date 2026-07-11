# task_graph_engine.py
from collections import defaultdict, deque

class TaskGraphEngine:
    """
    FEAT-087: Task Graph Engine
    Compiles task lists, resolves topological dependencies, and detects circular loops.
    """
    def __init__(self):
        self.adj = defaultdict(list)
        self.in_degree = defaultdict(int)
        self.priorities = {}
        self.nodes = set()

    def add_task(self, task_id: str, priority: int = 0) -> None:
        self.nodes.add(task_id)
        self.priorities[task_id] = priority
        if task_id not in self.in_degree:
            self.in_degree[task_id] = 0

    def add_dependency(self, parent_id: str, child_id: str) -> None:
        self.add_task(parent_id)
        self.add_task(child_id)
        self.adj[parent_id].append(child_id)
        self.in_degree[child_id] += 1

    def has_cycle(self) -> bool:
        """
        Kahn's Algorithm for cycle check.
        """
        in_deg = self.in_degree.copy()
        queue = deque([n for n in self.nodes if in_deg[n] == 0])
        visited_count = 0
        
        while queue:
            node = queue.popleft()
            visited_count += 1
            for neighbor in self.adj[node]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    queue.append(neighbor)
                    
        return visited_count != len(self.nodes)

    def get_schedule(self) -> list[str]:
        """
        Returns topological ordering sorted by task priority.
        """
        if self.has_cycle():
            raise ValueError("Circular dependency detected in Task Graph")
            
        in_deg = self.in_degree.copy()
        # Find all nodes with 0 in-degree and sort by priority descending
        zero_in_degree = [n for n in self.nodes if in_deg[n] == 0]
        zero_in_degree.sort(key=lambda x: self.priorities.get(x, 0), reverse=True)
        
        schedule = []
        while zero_in_degree:
            # Pick highest priority node
            node = zero_in_degree.pop(0)
            schedule.append(node)
            for neighbor in self.adj[node]:
                in_deg[neighbor] -= 1
                if in_deg[neighbor] == 0:
                    zero_in_degree.append(neighbor)
            zero_in_degree.sort(key=lambda x: self.priorities.get(x, 0), reverse=True)
            
        return schedule
