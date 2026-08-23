import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))

from task_graph_engine import TaskGraphEngine

def test_task_graph_topological_sort():
    engine = TaskGraphEngine()
    engine.add_task("Task 1.1", priority=1)
    engine.add_task("Task 1.2", priority=2)
    engine.add_dependency("Task 1.1", "Task 1.2")
    
    schedule = engine.get_schedule()
    assert schedule == ["Task 1.1", "Task 1.2"]

def test_task_graph_circular_dependency():
    engine = TaskGraphEngine()
    engine.add_dependency("A", "B")
    engine.add_dependency("B", "C")
    engine.add_dependency("C", "A")
    
    assert engine.has_cycle() is True
    with pytest.raises(ValueError):
        engine.get_schedule()
