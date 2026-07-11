# File path: tests/unit/test_pathfinder.py
import unittest
from vir_runtime.planner.graph import StateTransitionGraph
from vir_runtime.planner.pathfinder import Pathfinder, GoalUnreachableError

class TestPathfinder(unittest.TestCase):
    def setUp(self):
        self.graph = StateTransitionGraph()
        # Create transitions: A -> B (action1) -> C (action2)
        self.graph.add_edge("A", "B", {"type": "click", "selector": "#next"})
        self.graph.add_edge("B", "C", {"type": "click", "selector": "#submit"})
        self.pathfinder = Pathfinder(self.graph)

    def test_find_shortest_path(self):
        path = self.pathfinder.find_shortest_path("A", "C")
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0]["selector"], "#next")
        self.assertEqual(path[1]["selector"], "#submit")

    def test_goal_unreachable(self):
        self.graph.add_node("D")
        with self.assertRaises(GoalUnreachableError):
            self.pathfinder.find_shortest_path("A", "D")

    def test_backtrack_route(self):
        # From C, backtrack should trace back to B and then A
        # C parent is B (via action2), B parent is A (via action1)
        route = self.graph.get_backtrack_route("C")
        self.assertEqual(len(route), 2)
        self.assertEqual(route[0]["selector"], "#next")
        self.assertEqual(route[1]["selector"], "#submit")

if __name__ == "__main__":
    unittest.main()
