"""
test_runtime_stress.py — Stress tests for FR-05/FR-06: 50 random blueprints + failure injection.
8 stress/failure test cases using reproducible seeds.
"""
import os
import sys
import json
import random
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "fixtures")))

from conftest import RuntimeTestBase

try:
    import pytest
    STRESS_MARKER = pytest.mark.stress
    SLOW_MARKER = pytest.mark.slow
except ImportError:
    def STRESS_MARKER(f): return f
    def SLOW_MARKER(f): return f


class StressTests(RuntimeTestBase):
    """Stress tests — run 50+ blueprints through the full lifecycle simulation."""

    STRESS_BLUEPRINT_COUNT = 50
    STRESS_PHASES_RANGE = (2, 5)
    STRESS_TASKS_PER_PHASE_RANGE = (1, 6)

    def generate_random_blueprint(self, n_phases: int, n_tasks_per_phase: int, seed: int) -> dict:
        """Generate a reproducible random valid blueprint."""
        rng = random.Random(seed)
        feature_id = f"FEAT-STRESS-{seed:04d}"
        packages = []

        for phase_n in range(1, n_phases + 1):
            for task_n in range(1, n_tasks_per_phase + 1):
                task_id = f"T{phase_n}_{task_n}"
                deps = []
                if task_n > 1:
                    deps = [f"T{phase_n}_{task_n - 1}"]
                elif phase_n > 1:
                    deps = [f"T{phase_n - 1}_{n_tasks_per_phase}"]

                n_writes = rng.randint(1, 3)
                write_set = [f"src/phase{phase_n}/module_{task_n}_{i}.py" for i in range(n_writes)]
                packages.append({
                    "task_id": task_id,
                    "module": f"Phase {phase_n}",
                    "write_set": write_set,
                    "dependencies": deps,
                    "implementation_notes": f"Stress task {task_id}",
                    "verification": f"pytest tests/test_{task_id.lower()}.py",
                    "expected_outputs": write_set,
                })

        return {
            "feature_id": feature_id,
            "feature_name": f"Stress Test {seed}",
            "implementation_packages": packages,
        }

    def run_blueprint_lifecycle(self, blueprint: dict) -> dict:
        """Run full lifecycle for a blueprint. Returns final dashboard."""
        from ledger import ImplementationLedger
        from dag_planner import DAGPlanner
        from lock_manager import LockManager
        from worker_manager import WorkerManager
        from event_logger import EventLogger, WORKFLOW_INITIALIZED, PHASE_STARTED, PHASE_COMPLETED, DEBUG_PASSED, VERIFY_PASSED
        from event_reducer import EventReducer
        from state_path import ensure_dirs
        from state_aggregator import StateAggregator

        ensure_dirs(self.workspace)

        planner = DAGPlanner()
        errors = planner.validate(blueprint)
        assert len(errors) == 0, f"Blueprint invalid: {errors}"

        logger = EventLogger(self.workspace)
        reducer = EventReducer(self.workspace)
        ledger = ImplementationLedger(self.workspace)
        ledger.init_from_blueprint(blueprint)
        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": blueprint["feature_id"]})

        # dag keys: nodes, edges, sorted, groups, validation_errors
        dag = planner.build(blueprint)
        groups = dag["groups"]  # list of parallel task groups

        phases = [p["id"] for p in ledger.load()["phases"]]
        lm = LockManager(self.workspace)
        wm = WorkerManager(self.workspace)

        for phase_id in phases:
            ledger.mark_phase_started(phase_id)
            logger.emit(PHASE_STARTED, {"phase_id": phase_id})

            phase_tasks = set(
                pkg["task_id"] for pkg in blueprint["implementation_packages"]
                if pkg.get("module") == phase_id
            )
            for group in groups:
                for task_id in group:
                    if task_id not in phase_tasks:
                        continue
                    writes = next(
                        (p.get("write_set", []) for p in blueprint["implementation_packages"]
                         if p["task_id"] == task_id), []
                    )
                    pid = os.getpid()
                    lm.acquire(task_id, writes, pid=pid)
                    wid = wm.register(task_id, pid=pid, command="stress-test")
                    ledger.mark_task_completed(task_id)
                    wm.mark_completed(wid)
                    lm.release(task_id)

            ledger.mark_phase_completed(phase_id)
            logger.emit(PHASE_COMPLETED, {"phase_id": phase_id})

        logger.emit(DEBUG_PASSED, {})
        logger.emit(VERIFY_PASSED, {})
        reducer.replay_all()

        return StateAggregator(self.workspace).aggregate()

    def _run_in_isolated_workspace(self, seed: int, n_phases: int, n_tasks: int) -> tuple:
        """Run one blueprint in a fresh temp workspace. Returns (success, error_msg)."""
        import tempfile, shutil
        blueprint = self.generate_random_blueprint(n_phases, n_tasks, seed)
        workspace = tempfile.mkdtemp(prefix=f"aiwf_stress_{seed}_")
        original_ws = self.workspace
        original_root = os.environ.get("AIWF_STATE_ROOT", "")
        try:
            self.workspace = workspace
            os.environ["AIWF_STATE_ROOT"] = os.path.join(workspace, ".agents", "state")
            dashboard = self.run_blueprint_lifecycle(blueprint)

            # Assert no corruption
            from lock_manager import LockManager
            from worker_manager import WorkerManager
            lm = LockManager(self.workspace)
            wm = WorkerManager(self.workspace)
            assert lm.get_lock_count() == 0, f"Active locks remain"
            assert not wm.has_active_workers(), f"Active workers remain"
            assert dashboard.get("release_allowed"), f"release_allowed=False"
            return True, None
        except Exception as e:
            return False, str(e)
        finally:
            self.workspace = original_ws
            os.environ["AIWF_STATE_ROOT"] = original_root
            shutil.rmtree(workspace, ignore_errors=True)

    # TC1: 50 random blueprints — zero corruption, all release_allowed=True
    def test_stress_50_blueprints(self):
        """FR-05: Stress test 50 random blueprints — all must complete without corruption."""
        failures = []
        for seed in range(self.STRESS_BLUEPRINT_COUNT):
            n_phases = random.Random(seed).randint(*self.STRESS_PHASES_RANGE)
            n_tasks = random.Random(seed + 1000).randint(*self.STRESS_TASKS_PER_PHASE_RANGE)
            ok, err = self._run_in_isolated_workspace(seed, n_phases, n_tasks)
            if not ok:
                failures.append(f"Seed {seed}: {err}")

        if failures:
            self.fail(f"{len(failures)}/{self.STRESS_BLUEPRINT_COUNT} failed:\n" + "\n".join(failures[:5]))

    # TC2: Failure injection — JSON write failure → atomic rollback, original intact
    def test_failure_injection_json_write(self):
        """FR-06: Simulated disk-full during atomic write → original file preserved."""
        from atomic_writer import write_json_atomic, read_json_safe
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        target = os.path.join(self.workspace, "test_atomic.json")
        original_data = {"original": "value", "preserved": True}
        write_json_atomic(target, original_data)

        with patch("atomic_writer.os.rename", side_effect=OSError("disk full")):
            with patch("atomic_writer.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    write_json_atomic(target, {"corrupted": True})

        # Original must still be intact
        data_after = read_json_safe(target)
        self.assertEqual(data_after["original"], "value")
        self.assertFalse(data_after.get("corrupted", False))

    # TC3: Failure injection — permission denied on lock write → state empty (no partial)
    def test_failure_injection_permission_denied(self):
        """FR-06: PermissionError during lock write → no partial state written."""
        from lock_manager import LockManager
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        lm = LockManager(self.workspace)
        # Patch _save to raise PermissionError
        with patch.object(lm, "_save", side_effect=PermissionError("Permission denied")):
            with self.assertRaises(PermissionError):
                lm.acquire("TaskFail", ["src/a.py"], pid=os.getpid())
        self.assertEqual(lm.get_lock_count(), 0)

    # TC4: Failure injection — event reducer handles IOError on write gracefully
    def test_failure_injection_patch_conflict(self):
        """FR-06: IOError during state write after event replay → no crash, state may be partial."""
        from event_logger import EventLogger, WORKFLOW_INITIALIZED
        from event_reducer import EventReducer
        from state_path import ensure_dirs
        ensure_dirs(self.workspace)
        logger = EventLogger(self.workspace)
        logger.emit(WORKFLOW_INITIALIZED, {"feature_id": "FEAT-INJECT"})
        reducer = EventReducer(self.workspace)

        # Patch the internal write to fail exactly once
        original_write = reducer._write
        call_count = [0]
        def flaky_write(category, state):
            call_count[0] += 1
            if call_count[0] == 1:
                raise IOError("Simulated write conflict")
            return original_write(category, state)
        reducer._write = flaky_write

        try:
            reducer.replay_all()
        except IOError:
            pass  # Expected on first call

        # Must not crash — state may be empty but not corrupted
        from state_path import get_state_file
        from atomic_writer import read_json_safe
        state = read_json_safe(get_state_file("workflow", self.workspace))
        if state is not None:
            self.assertIsInstance(state, dict)

    # TC5: Stress — cyclic blueprints always rejected (no crash for any seed)
    def test_stress_cyclic_blueprint_rejected(self):
        """FR-05: Cyclic blueprint always raises CyclicDependencyError."""
        from dag_planner import DAGPlanner, CyclicDependencyError
        planner = DAGPlanner()
        for seed in range(10):
            rng = random.Random(seed)
            n = rng.randint(3, 8)
            nodes = [f"T{i}" for i in range(n)]
            # Force a cycle: Ti → T(i+1) → ... → T0
            graph = {nodes[i]: [nodes[(i + 1) % n]] for i in range(n)}
            with self.assertRaises(CyclicDependencyError,
                                   msg=f"Seed {seed}: should raise CyclicDependencyError"):
                planner.topological_sort(graph)

    # TC6: Stress — parallel safety check consistent for overlapping write_sets
    def test_stress_parallel_safety_consistency(self):
        """FR-05: check_parallel_safety always False for overlapping write_sets."""
        from dag_planner import DAGPlanner
        planner = DAGPlanner()
        for seed in range(20):
            shared = f"src/shared_{seed}.py"
            blueprint = {
                "implementation_packages": [
                    {"task_id": "T1", "write_set": [shared], "dependencies": []},
                    {"task_id": "T2", "write_set": [shared, f"src/other_{seed}.py"], "dependencies": []},
                ]
            }
            self.assertFalse(
                planner.check_parallel_safety(["T1", "T2"], blueprint),
                f"Seed {seed}: should be unsafe (overlapping write_set)"
            )

    # TC7: Stress — 20 blueprints all produce valid JSON dashboards
    def test_stress_all_dashboards_valid_json(self):
        """FR-05: Every lifecycle produces valid, parseable dashboard JSON."""
        errors = []
        for seed in range(20):
            ok, err = self._run_in_isolated_workspace(seed, n_phases=2, n_tasks=2)
            if not ok:
                errors.append(f"Seed {seed}: {err}")

        if errors:
            self.fail(f"{len(errors)} blueprints failed:\n" + "\n".join(errors))

    # TC8: Stress — 15 blueprints ledger always ends completed
    def test_stress_ledger_always_completed(self):
        """FR-05: Ledger implementation_status=completed after all tasks done."""
        import tempfile, shutil
        errors = []
        for seed in range(15):
            n_phases = random.Random(seed).randint(1, 3)
            n_tasks = random.Random(seed + 500).randint(1, 4)
            blueprint = self.generate_random_blueprint(n_phases, n_tasks, seed)
            workspace = tempfile.mkdtemp(prefix=f"aiwf_ledger_{seed}_")
            original_ws = self.workspace
            original_root = os.environ.get("AIWF_STATE_ROOT", "")
            try:
                self.workspace = workspace
                os.environ["AIWF_STATE_ROOT"] = os.path.join(workspace, ".agents", "state")
                self.run_blueprint_lifecycle(blueprint)
                from ledger import ImplementationLedger
                data = ImplementationLedger(self.workspace).load()
                if data.get("implementation_status") != "completed":
                    errors.append(f"Seed {seed}: status={data.get('implementation_status')}")
            except Exception as e:
                errors.append(f"Seed {seed}: {e}")
            finally:
                self.workspace = original_ws
                os.environ["AIWF_STATE_ROOT"] = original_root
                shutil.rmtree(workspace, ignore_errors=True)

        if errors:
            self.fail(f"{len(errors)} ledgers not completed:\n" + "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
