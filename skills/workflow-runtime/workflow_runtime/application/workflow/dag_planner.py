# dag_planner.py
"""
DAG-based execution planner for AIWF implementation tasks.
Parses blueprint JSON tasks and dependencies, produces topologically sorted
execution groups. Validates for cycles, missing references, and security violations.
"""
from __future__ import annotations

import os
from typing import Any, cast


class CyclicDependencyError(ValueError):
    """Raised when a dependency cycle is detected in the task DAG."""


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

    def build(self, blueprint: dict[str, Any]) -> dict[str, Any]:
        raw_pkgs = blueprint.get("implementation_packages")
        packages: list[dict[str, Any]] = [cast(dict[str, Any], p) for p in cast(list[Any], raw_pkgs) if isinstance(p, dict)] if isinstance(raw_pkgs, list) else []

        nodes: dict[str, dict[str, Any]] = {}
        for pkg in packages:
            task_id = str(pkg.get("task_id", ""))
            if not task_id:
                continue
            nodes[task_id] = {
                "task_id": task_id,
                "module": str(pkg.get("module", "")),
                "read_set": pkg.get("read_set", []),
                "write_set": pkg.get("write_set", []),
                "dependencies": pkg.get("dependencies", []),
                "implementation_notes": str(pkg.get("implementation_notes", "")),
                "verification": str(pkg.get("verification", "")),
                "rollback": str(pkg.get("rollback", "")),
                "expected_outputs": pkg.get("expected_outputs", []),
            }

        edges: dict[str, list[str]] = {
            task_id: [str(d) for d in cast(list[Any], node.get("dependencies", []))] if isinstance(node.get("dependencies"), list) else []
            for task_id, node in nodes.items()
        }

        validation_errors = self.validate(blueprint)
        sorted_tasks = self.topological_sort(edges)
        groups = self.get_execution_groups(edges)

        return {
            "nodes": nodes,
            "edges": edges,
            "sorted": sorted_tasks,
            "groups": groups,
            "validation_errors": validation_errors,
        }

    def topological_sort(self, graph: dict[str, list[str]]) -> list[str]:
        in_degree: dict[str, int] = {node: 0 for node in graph}
        adj: dict[str, list[str]] = {node: [] for node in graph}

        for task_id, deps in graph.items():
            for dep in deps:
                if dep in adj:
                    adj[dep].append(task_id)
                    in_degree[task_id] += 1

        queue = [t for t, d in in_degree.items() if d == 0]
        queue.sort()
        result: list[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in sorted(adj.get(node, [])):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    queue.sort()

        if len(result) != len(graph):
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
        if not graph:
            return []

        levels: dict[str, int] = {}

        def compute_level(task_id: str, visited: set[str]) -> int:
            if task_id in levels:
                return levels[task_id]
            if task_id in visited:
                return 0
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

        max_level = max(levels.values()) if levels else 0
        groups: list[list[str]] = [[] for _ in range(max_level + 1)]
        for task_id, level in levels.items():
            groups[level].append(task_id)

        return [sorted(g) for g in groups if g]

    def validate(self, blueprint: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        raw_pkgs = blueprint.get("implementation_packages")
        packages: list[dict[str, Any]] = [cast(dict[str, Any], p) for p in cast(list[Any], raw_pkgs) if isinstance(p, dict)] if isinstance(raw_pkgs, list) else []

        all_task_ids = {
            str(pkg.get("task_id", "")) for pkg in packages if pkg.get("task_id")
        }

        for pkg in packages:
            task_id = str(pkg.get("task_id", ""))
            if not task_id:
                errors.append("Found implementation_package with no 'task_id' field.")
                continue

            raw_deps = pkg.get("dependencies")
            deps = [str(d) for d in cast(list[Any], raw_deps)] if isinstance(raw_deps, list) else []
            for dep in deps:
                if dep not in all_task_ids:
                    errors.append(
                        f"Task '{task_id}' has missing dependency: '{dep}'."
                    )

            raw_writes = pkg.get("write_set")
            writes = [str(w) for w in cast(list[Any], raw_writes)] if isinstance(raw_writes, list) else []
            for path in writes:
                # A blueprint can be authored on POSIX and executed on Windows.
                # Treat both drive-qualified and slash-rooted paths as absolute.
                if os.path.isabs(path) or path.startswith(("/", "\\")):
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
        blueprint: dict[str, Any],
    ) -> bool:
        raw_pkgs = blueprint.get("implementation_packages")
        packages: list[dict[str, Any]] = [cast(dict[str, Any], p) for p in cast(list[Any], raw_pkgs) if isinstance(p, dict)] if isinstance(raw_pkgs, list) else []
        task_map = {str(p.get("task_id", "")): p for p in packages}

        write_sets: list[set[str]] = []

        for task_id in tasks:
            pkg = task_map.get(task_id)
            if pkg is None:
                return False

            raw_ws = pkg.get("write_set")
            ws_list = [str(w) for w in cast(list[Any], raw_ws)] if isinstance(raw_ws, list) else []
            write_set = set(ws_list)

            if not write_set:
                return False

            for path in write_set:
                basename = os.path.basename(path)
                if basename in GLOBAL_FILES or path in GLOBAL_FILES:
                    return False

            write_sets.append(write_set)

        for i in range(len(write_sets)):
            for j in range(i + 1, len(write_sets)):
                if write_sets[i] & write_sets[j]:
                    return False

        return True


__all__ = ["CyclicDependencyError", "DAGPlanner", "GLOBAL_FILES"]
