"""
test_dag_planner.py — Tests for FEAT-052 DAGPlanner (topological sort, cycle detection, validation).
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class DAGPlannerTests(RuntimeTestBase):

    def _load_multi_phase_fixture(self):
        return self.load_fixture("blueprints/FEAT-999_multi_phase_blueprint.json")

    def _load_broken_fixture(self):
        return self.load_fixture("blueprints/FEAT-997_broken_blueprint.json")

    # TC1: Simple 3-task chain sorts correctly
    def test_topological_sort_simple_chain(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        graph = {"T1": [], "T2": ["T1"], "T3": ["T2"]}
        result = planner.topological_sort(graph)
        self.assertEqual(result, ["T1", "T2", "T3"])

    # TC2: Cycle raises CyclicDependencyError
    def test_cycle_raises_error(self):
        from dag_planner import DAGPlanner, CyclicDependencyError
        planner = DAGPlanner()
        with self.assertRaises(CyclicDependencyError):
            planner.topological_sort({"A": ["B"], "B": ["A"]})

    # TC3: build() on multi-phase fixture produces correct nodes
    def test_build_multi_phase_fixture(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        blueprint = self._load_multi_phase_fixture()
        result = planner.build(blueprint)
        self.assertIn("nodes", result)
        self.assertGreaterEqual(len(result["nodes"]), 15)
        self.assertIn("Task 1.1", result["nodes"])

    # TC4: Execution groups from simple chain — 3 separate groups
    def test_execution_groups_chain(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        graph = {"T1": [], "T2": ["T1"], "T3": ["T2"]}
        groups = planner.get_execution_groups(graph)
        self.assertEqual(len(groups), 3)
        self.assertEqual(groups[0], ["T1"])

    # TC5: Parallel tasks in same group
    def test_parallel_candidates_in_same_group(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        # T1 and T2 have no deps → both in group 0
        graph = {"T1": [], "T2": [], "T3": ["T1", "T2"]}
        groups = planner.get_execution_groups(graph)
        self.assertIn("T1", groups[0])
        self.assertIn("T2", groups[0])

    # TC6: validate() detects broken blueprint errors
    def test_validate_broken_blueprint(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        blueprint = self._load_broken_fixture()
        errors = planner.validate(blueprint)
        # Must detect: absolute path, missing task_id, path traversal, missing dep
        self.assertGreater(len(errors), 0)
        error_text = " ".join(errors)
        self.assertIn("absolute", error_text.lower())

    # TC7: validate() passes for valid multi-phase blueprint
    def test_validate_valid_blueprint_no_errors(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        blueprint = {
            "implementation_packages": [
                {"task_id": "T1", "dependencies": [], "write_set": ["src/a.py"]},
                {"task_id": "T2", "dependencies": ["T1"], "write_set": ["src/b.py"]},
            ]
        }
        errors = planner.validate(blueprint)
        self.assertEqual(errors, [])

    # TC8: check_parallel_safety — non-overlapping write_sets = True
    def test_parallel_safety_non_overlapping(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        blueprint = {
            "implementation_packages": [
                {"task_id": "T1", "write_set": ["src/a.py"], "dependencies": []},
                {"task_id": "T2", "write_set": ["src/b.py"], "dependencies": []},
            ]
        }
        self.assertTrue(planner.check_parallel_safety(["T1", "T2"], blueprint))

    # TC9: check_parallel_safety — overlapping write_sets = False
    def test_parallel_safety_overlapping(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        blueprint = {
            "implementation_packages": [
                {"task_id": "T1", "write_set": ["src/a.py"], "dependencies": []},
                {"task_id": "T2", "write_set": ["src/a.py"], "dependencies": []},
            ]
        }
        self.assertFalse(planner.check_parallel_safety(["T1", "T2"], blueprint))

    # TC10: check_parallel_safety — global file = False
    def test_parallel_safety_global_file(self):
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        blueprint = {
            "implementation_packages": [
                {"task_id": "T1", "write_set": ["package.json"], "dependencies": []},
                {"task_id": "T2", "write_set": ["src/b.py"], "dependencies": []},
            ]
        }
        self.assertFalse(planner.check_parallel_safety(["T1", "T2"], blueprint))


if __name__ == "__main__":
    unittest.main()
