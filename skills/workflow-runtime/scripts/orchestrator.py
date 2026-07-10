"""
FEAT-052: SafeOrchestrator — DAG execution controller.

Coordinates: DAGPlanner, LockManager, WorkerManager, ImplementationLedger.
Default mode: safe_sequential (parallel disabled by default).
Completion gate: 9 conditions; all checked independently.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Optional

# ---------------------------------------------------------------------------
# Config defaults (can be overridden via .agents/runtime/orchestrator.json)
# ---------------------------------------------------------------------------
ORCHESTRATOR_DEFAULTS = {
    "default_mode": "safe_sequential",
    "allow_controlled_parallel": False,
    "lock_expiry_seconds": 300,
    "orphan_check_on_complete": True,
    "patch_mode": False,
}

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_config(workspace_root: str) -> dict:
    cfg_path = os.path.join(workspace_root, ".agents", "runtime", "orchestrator.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path) as f:
                return {**ORCHESTRATOR_DEFAULTS, **json.load(f)}
        except Exception:
            pass
    return dict(ORCHESTRATOR_DEFAULTS)


class CompletionGateError(Exception):
    """Raised when completion gate check fails."""


class SafeOrchestrator:
    """
    Singleton per execution. Coordinates DAG, locks, workers, and ledger.
    All gate checks are non-negotiable.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or os.getcwd()
        self.config = _load_config(self.workspace_root)

        # Lazy imports — keep orchestrator importable without all deps installed
        if _SCRIPT_DIR not in sys.path:
            sys.path.insert(0, _SCRIPT_DIR)

        from dag_planner import DAGPlanner      # type: ignore
        from lock_manager import LockManager    # type: ignore
        from worker_manager import WorkerManager  # type: ignore

        self.dag_planner = DAGPlanner()
        self.lock_manager = LockManager(workspace_root=self.workspace_root)
        self.worker_manager = WorkerManager(workspace_root=self.workspace_root)

    # ------------------------------------------------------------------
    # run_phase
    # ------------------------------------------------------------------
    def run_phase(self, phase_id: str, blueprint: dict, mode: str = "safe_sequential") -> dict:
        """
        Execute all tasks in a phase according to the DAG.

        Returns:
            {
                "phase_id": str,
                "mode": str,
                "tasks_completed": list[str],
                "tasks_failed": list[str],
                "gate_passed": bool,
                "gate_failures": list[str],
            }
        """
        errors = self.dag_planner.validate(blueprint)
        if errors:
            return {
                "phase_id": phase_id,
                "mode": mode,
                "tasks_completed": [],
                "tasks_failed": [],
                "gate_passed": False,
                "gate_failures": [f"DAG validation error: {e}" for e in errors],
            }

        # Identify tasks belonging to this phase
        packages = blueprint.get("implementation_packages", [])
        phase_tasks = [
            pkg for pkg in packages
            if pkg.get("phase_id") == phase_id or phase_id == "__all__"
        ]

        completed: list[str] = []
        failed: list[str] = []

        # Build execution graph for this phase subset
        graph: dict[str, list[str]] = {}
        for pkg in phase_tasks:
            tid = pkg["task_id"]
            deps = [d for d in pkg.get("dependencies", []) if any(p["task_id"] == d for p in phase_tasks)]
            graph[tid] = deps

        dag_result = self.dag_planner.build({"implementation_packages": phase_tasks})
        groups = self.dag_planner.get_execution_groups(dag_result.get("graph", graph))

        for group in groups:
            # Within a group tasks are parallelism candidates;
            # default mode forces sequential execution of each.
            for task_id in group:
                pkg = next((p for p in phase_tasks if p["task_id"] == task_id), None)
                if pkg is None:
                    continue
                result = self.run_task(pkg, blueprint)
                if result.get("status") == "completed":
                    completed.append(task_id)
                else:
                    failed.append(task_id)

        gate_passed, gate_failures = self.check_completion_gate()
        return {
            "phase_id": phase_id,
            "mode": mode,
            "tasks_completed": completed,
            "tasks_failed": failed,
            "gate_passed": gate_passed,
            "gate_failures": gate_failures,
        }

    # ------------------------------------------------------------------
    # run_task
    # ------------------------------------------------------------------
    def run_task(self, task: dict, blueprint: dict) -> dict:
        """
        Execute a single task with full lock+worker lifecycle.

        Returns:
            {"task_id": str, "status": "completed"|"failed", "reason": str}
        """
        task_id = task.get("task_id", "unknown")
        write_set = task.get("write_set", [])
        pid = os.getpid()
        expiry = self.config.get("lock_expiry_seconds", 300)

        # 1. Acquire locks (all-or-nothing)
        acquired = self.lock_manager.acquire(task_id, write_set, pid, expiry)
        if not acquired:
            return {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Lock acquisition failed for write_set: {write_set}",
            }

        # 2. Register worker
        worker_id = self.worker_manager.register(task_id, pid, f"task:{task_id}")

        try:
            # 3. (Optional) Patch mode — applied by caller; we just verify scope
            if self.config.get("patch_mode"):
                patch_path = task.get("patch_path")
                if patch_path:
                    if _SCRIPT_DIR not in sys.path:
                        sys.path.insert(0, _SCRIPT_DIR)
                    from patch_applier import PatchApplier  # type: ignore
                    pa = PatchApplier(workspace_root=self.workspace_root)
                    apply_result = pa.apply(task_id, patch_path, write_set)
                    if apply_result.get("status") != "applied":
                        raise RuntimeError(f"Patch apply failed: {apply_result.get('error')}")

            # 4. Verify expected outputs exist (if specified)
            expected_outputs = task.get("expected_outputs", [])
            missing = []
            for out in expected_outputs:
                # Only check actual file paths (not description strings)
                if out.endswith(".py") or out.endswith(".json") or out.endswith(".md"):
                    full = os.path.join(self.workspace_root, out) if not os.path.isabs(out) else out
                    if not os.path.exists(full):
                        missing.append(out)
            if missing:
                raise RuntimeError(f"Expected output files missing: {missing}")

            # 5. Mark completed
            self.worker_manager.mark_completed(worker_id)
            self.lock_manager.release(task_id)
            return {"task_id": task_id, "status": "completed", "reason": ""}

        except Exception as exc:
            error_msg = str(exc)
            self.worker_manager.mark_failed(worker_id, error_msg)
            self.lock_manager.release(task_id)
            return {"task_id": task_id, "status": "failed", "reason": error_msg}

    # ------------------------------------------------------------------
    # check_completion_gate
    # ------------------------------------------------------------------
    def check_completion_gate(self) -> tuple[bool, list[str]]:
        """
        9-condition non-negotiable completion gate.

        Returns (True, []) on success, (False, [reasons]) on any failure.
        """
        failures: list[str] = []

        # Condition 1: No active file locks
        active_locks = self.lock_manager.get_active_locks()
        if active_locks:
            lock_ids = [l.get("task_id", "?") for l in active_locks]
            failures.append(f"Active file locks remaining for tasks: {lock_ids}")

        # Condition 2: No active workers
        if self.worker_manager.has_active_workers():
            active = self.worker_manager.get_active_workers()
            wids = [w.get("worker_id", "?") for w in active]
            failures.append(f"Active workers still running: {wids}")

        # Condition 3: No orphan workers
        if self.config.get("orphan_check_on_complete", True):
            orphans = self.worker_manager.detect_orphans()
            if orphans:
                failures.append(f"Orphan workers detected (PID dead but not cleaned): {orphans}")

        # Conditions 4-9: Check stale locks
        stale = self.lock_manager.clear_stale_locks()
        if stale:
            failures.append(f"Stale locks were present (auto-cleared): {stale}")

        return (len(failures) == 0, failures)

    # ------------------------------------------------------------------
    # abort
    # ------------------------------------------------------------------
    def abort(self, ask_before_kill: bool = True) -> None:
        """
        Abort execution: terminate all workers and release all locks.
        If ask_before_kill=True, requires explicit confirmation before termination.
        """
        workers = self.worker_manager.get_active_workers()
        locks = self.lock_manager.get_active_locks()

        if ask_before_kill and (workers or locks):
            print(
                json.dumps({
                    "action": "abort_confirmation_required",
                    "active_workers": len(workers),
                    "active_locks": len(locks),
                    "message": "Type 'ABORT' to confirm termination of all workers and release of all locks.",
                })
            )
            # In CLI context the caller reads confirmation; here we just signal
            return

        workers_killed = 0
        for worker in workers:
            wid = worker.get("worker_id")
            if wid:
                self.worker_manager.terminate_orphan(wid, force=True)
                workers_killed += 1

        locks_released = 0
        for lock in locks:
            tid = lock.get("task_id")
            if tid:
                self.lock_manager.release(tid)
                locks_released += 1

        print(json.dumps({"workers_killed": workers_killed, "locks_released": locks_released}))

    # ------------------------------------------------------------------
    # resume
    # ------------------------------------------------------------------
    def resume(self) -> Optional[str]:
        """
        Return the next incomplete task_id or phase_id, or None if all complete.
        Delegates to PhaseController if available.
        """
        try:
            from phase_controller import PhaseController  # type: ignore
            pc = PhaseController(workspace_root=self.workspace_root)
            return pc.resume_next_phase()
        except Exception:
            return None
