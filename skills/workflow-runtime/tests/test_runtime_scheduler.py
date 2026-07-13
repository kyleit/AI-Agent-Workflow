# test_runtime_scheduler.py
import unittest
import os
import sys
import json
import time
from unittest.mock import patch, MagicMock

# Add scripts path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))

from adaptive_scheduler import AdaptiveTeamPlanner, RuntimeScheduler, SchedulerMetrics

class TestRuntimeScheduler(unittest.TestCase):
    def test_mode_classification(self):
        planner = AdaptiveTeamPlanner()
        
        # Mode A: Git/release/bump tasks
        mode_a = planner.determine_execution_mode("git commit changes", [])
        self.assertEqual(mode_a, "A")
        
        # Mode C: Isolated write scopes (e.g. backend implementation)
        mode_c = planner.determine_execution_mode("backend implementation", ["sources/backend/"])
        self.assertEqual(mode_c, "C")
        
        # Mode B: Fallback research/planning
        mode_b = planner.determine_execution_mode("requirement discovery", ["docs/brainstorming/"])
        self.assertEqual(mode_b, "B")

    @patch("psutil.cpu_percent")
    @patch("psutil.virtual_memory")
    def test_adaptive_scaling(self, mock_virtual_mem, mock_cpu):
        planner = AdaptiveTeamPlanner()
        raw_tasks = [
            {"name": "task 1", "role": "development", "locks": ["sources/backend/"]}
        ]
        agents, graph, _ = planner.plan_team_and_graph("FEAT-118", raw_tasks)
        metrics = SchedulerMetrics()
        scheduler = RuntimeScheduler(agents, graph, metrics)
        
        # Case 1: High CPU/RAM load -> scale to 1 worker
        mock_cpu.return_value = 85.0
        mock_virtual_mem.return_value.percent = 30.0
        self.assertEqual(scheduler.scale_agents(), 1)
        
        # Case 2: Low load -> scale to default 4 workers
        mock_cpu.return_value = 10.0
        mock_virtual_mem.return_value.percent = 20.0
        self.assertEqual(scheduler.scale_agents(), 4)

    def test_reclaim_idle_agents(self):
        planner = AdaptiveTeamPlanner()
        raw_tasks = [
            {"name": "task 1", "role": "development", "locks": []},
            {"name": "task 2", "role": "test", "locks": []}
        ]
        agents, graph, _ = planner.plan_team_and_graph("FEAT-118", raw_tasks)
        metrics = SchedulerMetrics()
        
        # Set agent activity to old timestamp
        for a in agents.values():
            a["status"] = "IDLE"
            a["last_active"] = time.time() - 2.0
            
        scheduler = RuntimeScheduler(agents, graph, metrics)
        
        # Reclaim idle agents
        reclaimed = scheduler.reclaim_idle_agents(idle_timeout=1.0)
        
        # At least test/backend agents should be reclaimed
        self.assertTrue(len(reclaimed) > 0)
        # PM/Arch should not be reclaimed (or in this case, any agent missing "PM"/"ARCH" in ID)
        for rid in reclaimed:
            self.assertNotIn("PM", rid)
            self.assertNotIn("ARCH", rid)

    def test_stress_workload_metrics(self):
        # Create a large workload of 50 tasks
        raw_tasks = []
        for i in range(50):
            raw_tasks.append({
                "name": f"parallel implementation chunk {i}",
                "role": "development",
                "locks": [f"sources/backend/mod_{i}.py"],
                "dependencies": []
            })
            
        planner = AdaptiveTeamPlanner()
        agents, graph, planning_latency = planner.plan_team_and_graph("FEAT-118", raw_tasks)
        
        metrics = SchedulerMetrics()
        metrics.planning_latency = planning_latency
        
        scheduler = RuntimeScheduler(agents, graph, metrics)
        
        # Execute 50 tasks
        scheduler.execute_graph()
        
        # Verify metrics collected
        self.assertEqual(metrics.completed_tasks, 50)
        self.assertTrue(metrics.execution_latency > 0)
        self.assertTrue(metrics.throughput > 0)
        self.assertEqual(metrics.token_usage, 50 * 8000) # Mode C tasks allocate 8000 tokens each
        self.assertTrue(metrics.avg_cpu >= 0)
        self.assertTrue(metrics.avg_ram >= 0)

    def test_process_budget_limits(self):
        # Create 5 parallel Mode C tasks
        raw_tasks = []
        for i in range(5):
            raw_tasks.append({
                "name": f"mode c task {i}",
                "role": "development",
                "locks": [f"sources/backend/part_{i}.py"],
                "dependencies": []
            })
        planner = AdaptiveTeamPlanner()
        agents, graph, planning_latency = planner.plan_team_and_graph("FEAT-118", raw_tasks)
        
        # Enforce max_python_worker_processes = 2
        metrics = SchedulerMetrics()
        policy = {"max_python_worker_processes": 2}
        scheduler = RuntimeScheduler(agents, graph, metrics, policy=policy)
        
        # We intercept execute_task to check if active processes ever exceed 2
        orig_execute = scheduler.execute_task
        peak_processes = 0
        
        def spy_execute(task_id, *args, **kwargs):
            nonlocal peak_processes
            res = orig_execute(task_id, *args, **kwargs)
            peak_processes = max(peak_processes, len(scheduler.active_processes))
            return res
            
        scheduler.execute_task = spy_execute
        scheduler.execute_graph()
        
        self.assertEqual(metrics.completed_tasks, 5)
        self.assertTrue(peak_processes <= 2)



if __name__ == "__main__":
    unittest.main()
