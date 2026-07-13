# dag_planner.py
"""
DAG-based execution planner for AIWF implementation tasks.
Parses blueprint JSON tasks and dependencies, produces topologically sorted
execution groups. Validates for cycles, missing references, and security violations.
"""
from typing import Optional


class CyclicDependencyError(ValueError):
    """Raised when a dependency cycle is detected in the task DAG."""
    pass


# Files that always require sequential execution (cannot be parallelized)
GLOBAL_FILES = frozenset([
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "go.sum",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    ".agents/.session.json",
    ".agents/state/dashboard.json",
    ".agents/runtime/workers.json",
    ".agents/runtime/file-locks.json",
    ".agents/runtime/implementation-ledger.json",
])


class DAGPlanner:
    """
    Parses blueprint JSON into a dependency graph and produces
    topologically sorted execution groups.
    Pure algorithm — no file I/O except reading blueprint dict.
    """

    def build(self, blueprint: dict) -> dict:
        """
        Parse blueprint JSON into a DAG structure.
        
        Args:
            blueprint: Loaded JSON from FEAT-XXX_blueprint.json.
                Must contain 'implementation_packages' with task_id and dependencies.
        
        Returns:
            {
                nodes: {task_id: {...}},
                edges: {task_id: [deps]},
                groups: [[task_ids in execution order]],
                validation_errors: [],
            }
        
        Raises:
            CyclicDependencyError: If a dependency cycle is detected.
        """
        packages = blueprint.get("implementation_packages", [])

        # Build nodes dict
        nodes = {}
        for pkg in packages:
            task_id = pkg.get("task_id", "")
            if not task_id:
                continue
            nodes[task_id] = {
                "task_id": task_id,
                "module": pkg.get("module", ""),
                "read_set": pkg.get("read_set", []),
                "write_set": pkg.get("write_set", []),
                "dependencies": pkg.get("dependencies", []),
                "implementation_notes": pkg.get("implementation_notes", ""),
                "verification": pkg.get("verification", ""),
                "rollback": pkg.get("rollback", ""),
                "expected_outputs": pkg.get("expected_outputs", []),
            }

        # Build edges dict (task_id -> list of dependency task_ids)
        edges: dict[str, list[str]] = {
            task_id: node.get("dependencies", [])
            for task_id, node in nodes.items()
        }

        # Validate
        validation_errors = self.validate(blueprint)

        # Topological sort
        sorted_tasks = self.topological_sort(edges)

        # Compute execution groups
        groups = self.get_execution_groups(edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "sorted": sorted_tasks,
            "groups": groups,
            "validation_errors": validation_errors,
        }

    def topological_sort(self, graph: dict[str, list[str]]) -> list[str]:
        """
        Kahn's algorithm for topological sort.
        
        Args:
            graph: {task_id: [dependency_task_ids]}
        
        Returns:
            List of task_ids in topological order.
        
        Raises:
            CyclicDependencyError: If a cycle is detected.
        """
        # Build in-degree count and adjacency list
        in_degree: dict[str, int] = {node: 0 for node in graph}
        adj: dict[str, list[str]] = {node: [] for node in graph}

        for task_id, deps in graph.items():
            for dep in deps:
                if dep in adj:
                    adj[dep].append(task_id)
                    in_degree[task_id] += 1
                # Missing dep references are caught by validate()

        # Start with nodes that have no dependencies
        queue = [t for t, d in in_degree.items() if d == 0]
        queue.sort()  # Deterministic ordering
        result = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in sorted(adj.get(node, [])):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    queue.sort()

        if len(result) != len(graph):
            # Find nodes involved in cycle for better error message
            cycle_nodes = [n for n in graph if n not in result]
            raise CyclicDependencyError(
                f"Dependency cycle detected among tasks: {cycle_nodes}. "
                f"Fix circular dependencies in blueprint."
            )

        return result

    def get_execution_groups(
        self,
        graph: dict[str, list[str]],
    ) -> list[list[str]]:
        """
        Group tasks into execution levels where all deps of a group
        are satisfied by previous groups.
        Tasks in the same group are CANDIDATES for parallel execution
        (subject to parallel safety check).
        
        Returns:
            List of groups (each group is a list of task_ids).
        """
        if not graph:
            return []

        # Compute level for each node (longest dependency path)
        levels: dict[str, int] = {}

        def compute_level(task_id: str, visited: set) -> int:
            if task_id in levels:
                return levels[task_id]
            if task_id in visited:
                return 0  # Cycle guard (already caught by topological_sort)
            visited.add(task_id)
            deps = graph.get(task_id, [])
            if not deps:
                levels[task_id] = 0
            else:
                levels[task_id] = 1 + max(
                    compute_level(d, visited) for d in deps if d in graph
                )
            return levels[task_id]

        for task_id in graph:
            compute_level(task_id, set())

        # Invert: level -> list of tasks
        max_level = max(levels.values()) if levels else 0
        groups: list[list[str]] = [[] for _ in range(max_level + 1)]
        for task_id, level in levels.items():
            groups[level].append(task_id)

        # Sort within each group for determinism
        return [sorted(g) for g in groups if g]

    def validate(self, blueprint: dict) -> list[str]:
        """
        Validate blueprint for common issues.
        
        Returns:
            List of validation error strings (empty if valid).
        """
        errors = []
        packages = blueprint.get("implementation_packages", [])
        all_task_ids = {
            pkg.get("task_id", "") for pkg in packages if pkg.get("task_id")
        }

        for pkg in packages:
            task_id = pkg.get("task_id", "")
            if not task_id:
                errors.append("Found implementation_package with no 'task_id' field.")
                continue

            # Check dependency references exist
            for dep in pkg.get("dependencies", []):
                if dep not in all_task_ids:
                    errors.append(
                        f"Task '{task_id}' has missing dependency: '{dep}'."
                    )

            # Check write_set paths
            for path in pkg.get("write_set", []):
                import os
                if os.path.isabs(path):
                    errors.append(
                        f"Task '{task_id}' write_set contains absolute path: '{path}'. "
                        f"Only relative paths allowed."
                    )
                normalized = os.path.normpath(path)
                if normalized.startswith(".."):
                    errors.append(
                        f"Task '{task_id}' write_set contains path traversal: '{path}'."
                    )

        return errors

    def check_parallel_safety(
        self,
        tasks: list[str],
        blueprint: dict,
    ) -> bool:
        """
        Check if a group of tasks can safely run in parallel.
        Conditions for parallel safety:
          1. write_sets don't overlap.
          2. No task touches a GLOBAL file.
          3. All tasks have determined write_sets.
        
        Returns:
            True if all conditions met; False otherwise.
        """
        packages = blueprint.get("implementation_packages", [])
        task_map = {p.get("task_id", ""): p for p in packages}

        write_sets: list[set[str]] = []

        for task_id in tasks:
            pkg = task_map.get(task_id)
            if pkg is None:
                return False  # Unknown task → cannot validate

            write_set = set(pkg.get("write_set", []))

            if not write_set:
                return False  # Undetermined write_set → sequential only

            # Check for global files
            for path in write_set:
                import os
                basename = os.path.basename(path)
                if basename in GLOBAL_FILES or path in GLOBAL_FILES:
                    return False

            write_sets.append(write_set)

        # Check for overlapping write_sets
        for i in range(len(write_sets)):
            for j in range(i + 1, len(write_sets)):
                if write_sets[i] & write_sets[j]:
                    return False

        return True
