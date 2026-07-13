"""
test_task_dag_execution.py — Integration tests for FR-04: DAG + LockManager + WorkerManager end-to-end.
8 test cases covering full task execution with locks, workers, and phase progression.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase


class TaskDAGExecutionTests(RuntimeTestBase):

    def _run_full_phase(self, blueprint: dict, phase_id: str) -> dict:
        """
        Simulate a full phase execution using DAGPlanner.build() API:
        - dag['edges'] = dependency graph {task_id: [dep_ids]}
        - dag['sorted'] = topological order list
        - dag['groups'] = parallel execution groups list of lists
        """
        from dag_planner import DAGPlanner
        from lock_manager import LockManager
        from worker_manager import WorkerManager
        from ledger import ImplementationLedger
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)

        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        ledger.mark_phase_started(phase_id)

        planner = DAGPlanner()
        dag = planner.build(blueprint)
        # dag keys: nodes, edges, sorted, groups, validation_errors
        groups = dag["groups"]  # list of lists (parallel groups in topo order)

        lm = LockManager(self.workspace)
        wm = WorkerManager(self.workspace)

        # Get tasks in this phase
        phase_tasks = set(
            pkg["task_id"]
            for pkg in blueprint["implementation_packages"]
            if pkg.get("module") == phase_id
        )

        for group in groups:
            # Only process tasks in this phase
            phase_group = [t for t in group if t in phase_tasks]
            if not phase_group:
                continue

            # Get write sets per task
            task_writes = {
                pkg["task_id"]: pkg.get("write_set", [])
                for pkg in blueprint["implementation_packages"]
                if pkg["task_id"] in phase_group
            }

            for task_id in phase_group:
                writes = task_writes[task_id]
                pid = os.getpid()
                lm.acquire(task_id, writes, pid=pid)
                wid = wm.register(task_id, pid=pid, command=f"python build_{task_id}.py")
                ledger.mark_task_completed(task_id)
                wm.mark_completed(wid)
                lm.release(task_id)

        ledger.mark_phase_completed(phase_id)

        from state_aggregator import StateAggregator
        return StateAggregator(self.workspace).aggregate()

    # TC1: Single phase DAG execution — no locks remain
    def test_single_phase_no_locks_remain(self):
        from lock_manager import LockManager
        blueprint = self.make_ledger_blueprint("FEAT-DAG-1", n_phases=1, tasks_per_phase=3)
        self._run_full_phase(blueprint, "Phase 1")
        lm = LockManager(self.workspace)
        self.assertEqual(lm.get_lock_count(), 0)

    # TC2: After phase execution, no active workers remain
    def test_single_phase_no_active_workers(self):
        from worker_manager import WorkerManager
        blueprint = self.make_ledger_blueprint("FEAT-DAG-2", n_phases=1, tasks_per_phase=2)
        self._run_full_phase(blueprint, "Phase 1")
        wm = WorkerManager(self.workspace)
        self.assertFalse(wm.has_active_workers())

    # TC3: Phase controller recommends continue_implement when more phases remain
    def test_multi_phase_controller_recommends_continue(self):
        from phase_controller import PhaseController
        from ledger import ImplementationLedger
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        blueprint = self.make_ledger_blueprint("FEAT-DAG-3", n_phases=3, tasks_per_phase=1)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        ledger.mark_phase_started("Phase 1")
        ledger.mark_task_completed("Task 1.1")
        ledger.mark_phase_completed("Phase 1")
        pc = PhaseController(self.workspace)
        result = pc.on_phase_completed("Phase 1")
        self.assertEqual(result["next_action"], "continue_implement")
        self.assertEqual(result["next_phase_id"], "Phase 2")

    # TC4: DAG topological order — each task's deps appear before it
    def test_dag_respects_dependencies_across_phases(self):
        from dag_planner import DAGPlanner
        blueprint = self.load_fixture("blueprints/FEAT-999_multi_phase_blueprint.json")
        planner = DAGPlanner()
        dag = planner.build(blueprint)
        # dag['sorted'] = topological sort; dag['edges'] = {task_id: [deps]}
        edges = dag["edges"]
        sorted_tasks = dag["sorted"]

        pos = {task_id: i for i, task_id in enumerate(sorted_tasks)}
        for task_id, deps in edges.items():
            for dep in deps:
                if dep in pos and task_id in pos:
                    self.assertLess(
                        pos[dep], pos[task_id],
                        f"{dep} (pos={pos[dep]}) must come before {task_id} (pos={pos[task_id]})"
                    )

    # TC5: Parallel-safe tasks execute in same group without conflict
    def test_parallel_safe_tasks_same_group(self):
        from dag_planner import DAGPlanner
        blueprint = {
            "implementation_packages": [
                {"task_id": "T1", "module": "Phase 1", "write_set": ["src/a.py"], "dependencies": []},
                {"task_id": "T2", "module": "Phase 1", "write_set": ["src/b.py"], "dependencies": []},
                {"task_id": "T3", "module": "Phase 1", "write_set": ["src/c.py"], "dependencies": ["T1", "T2"]},
            ]
        }
        planner = DAGPlanner()
        dag = planner.build(blueprint)
        groups = dag["groups"]
        # T1 and T2 must be in same group (both parallel, no deps)
        self.assertIn("T1", groups[0])
        self.assertIn("T2", groups[0])
        self.assertIn("T3", groups[1])
        # Both parallel + non-overlapping → parallel safe
        self.assertTrue(planner.check_parallel_safety(["T1", "T2"], blueprint))

    # TC6: Lock conflict prevents parallel execution of overlapping write sets
    def test_lock_prevents_overlapping_write_set_execution(self):
        from lock_manager import LockManager
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        lm = LockManager(self.workspace)
        ok1 = lm.acquire("T1", ["src/shared.py"], pid=os.getpid())
        ok2 = lm.acquire("T2", ["src/shared.py", "src/other.py"], pid=os.getpid())
        self.assertTrue(ok1)
        self.assertFalse(ok2, "Overlapping write set must be blocked by lock")
        # src/other.py must NOT be locked (all-or-nothing)
        self.assertFalse(lm.has_conflict(["src/other.py"]))

    # TC7: Worker orphan detection during mid-phase failure
    def test_orphan_detected_mid_phase(self):
        from worker_manager import WorkerManager
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        wm = WorkerManager(self.workspace)
        wm.register("Task 1.1", pid=99999999, command="python crashed.py")
        orphans = wm.detect_orphans()
        self.assertEqual(len(orphans), 1)

    # TC8: Full 2-phase lifecycle — ledger ends with implementation_status=completed
    def test_full_2_phase_lifecycle_status_completed(self):
        from ledger import ImplementationLedger
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        blueprint = self.make_ledger_blueprint("FEAT-FULL", n_phases=2, tasks_per_phase=2)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)

        for phase_n in range(1, 3):
            phase_id = f"Phase {phase_n}"
            ledger.mark_phase_started(phase_id)
            for task_n in range(1, 3):
                ledger.mark_task_completed(f"Task {phase_n}.{task_n}")
            ledger.mark_phase_completed(phase_id)

        data = ledger.load()
        self.assertEqual(data["implementation_status"], "completed")


if __name__ == "__main__":
    unittest.main()
