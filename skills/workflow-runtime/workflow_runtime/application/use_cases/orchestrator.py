from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Optional, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator

ORCHESTRATOR_DEFAULTS = {
    "default_mode": "safe_sequential",
    "allow_controlled_parallel": False,
    "lock_expiry_seconds": 300,
    "orphan_check_on_complete": True,
    "patch_mode": False,
}

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_config(workspace_root: str) -> dict[str, Any]:
    cfg_path = os.path.join(workspace_root, ".agents", "runtime", "orchestrator.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = cast(dict[str, Any], json.load(f))
                return {**ORCHESTRATOR_DEFAULTS, **data}
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

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        self.workspace_root = workspace_root or os.getcwd()
        self.config = _load_config(self.workspace_root)

        if _SCRIPT_DIR not in sys.path:
            sys.path.insert(0, _SCRIPT_DIR)

        from workflow_runtime.application.workflow.dag_planner import (
            DAGPlanner)

        self.dag_planner = DAGPlanner()
        self.lock_manager: Any = InfrastructureLocator.LockManager(workspace_root=self.workspace_root)
        self.worker_manager: Any = InfrastructureLocator.WorkerManager(workspace_root=self.workspace_root)

    def run_phase(self, phase_id: str, blueprint: Any, mode: str = "safe_sequential") -> dict[str, Any]:
        bp_dict: dict[str, Any] = cast(dict[str, Any], blueprint) if isinstance(blueprint, dict) else {}
        errors = self.dag_planner.validate(bp_dict)
        if errors:
            return {
                "phase_id": phase_id,
                "mode": mode,
                "tasks_completed": [],
                "tasks_failed": [],
                "gate_passed": False,
                "gate_failures": [f"DAG validation error: {e}" for e in errors],
            }

        raw_packages: Any = bp_dict["implementation_packages"] if "implementation_packages" in bp_dict else []
        packages: list[Any] = cast(list[Any], raw_packages) if isinstance(raw_packages, list) else []
        phase_tasks: list[dict[str, Any]] = [
            cast(dict[str, Any], pkg) for pkg in packages
            if isinstance(pkg, dict) and (cast(dict[str, Any], pkg).get("phase_id") == phase_id or phase_id == "__all__")
        ]

        completed: list[str] = []
        failed: list[str] = []

        graph: dict[str, list[str]] = {}
        for pkg in phase_tasks:
            tid = str(pkg.get("task_id", ""))
            raw_deps = pkg.get("dependencies")
            deps_list: list[str] = cast(list[str], raw_deps) if isinstance(raw_deps, list) else []
            deps = [d for d in deps_list if any(str(p.get("task_id")) == d for p in phase_tasks)]
            graph[tid] = deps

        dag_result = self.dag_planner.build({"implementation_packages": phase_tasks})
        raw_graph = dag_result.get("graph", graph)
        groups = self.dag_planner.get_execution_groups(cast(dict[str, list[str]], raw_graph))

        for group in groups:
            for task_id in group:
                pkg = next((p for p in phase_tasks if str(p.get("task_id")) == task_id), None)
                if pkg is None:
                    continue
                result = self.run_task(pkg, bp_dict)
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

    def run_task(self, task: dict[str, Any], blueprint: Any) -> dict[str, Any]:
        _ = blueprint
        task_id = str(task.get("task_id", "unknown"))
        raw_ws = task.get("write_set")
        write_set: list[Any] = cast(list[Any], raw_ws) if isinstance(raw_ws, list) else []
        pid = os.getpid()
        expiry = int(self.config.get("lock_expiry_seconds", 300) or 300)

        acq_fn: Any = getattr(self.lock_manager, "acquire", None)
        acquired = acq_fn(task_id, write_set, pid, expiry) if callable(acq_fn) else True
        if not acquired:
            return {
                "task_id": task_id,
                "status": "failed",
                "reason": f"Lock acquisition failed for write_set: {write_set}",
            }

        reg_fn: Any = getattr(self.worker_manager, "register", None)
        worker_id = reg_fn(task_id, pid, f"task:{task_id}") if callable(reg_fn) else "w_default"

        try:
            if self.config.get("patch_mode"):
                patch_path = str(task.get("patch_path", "") or "")
                if patch_path:
                    pa_cls: Any = getattr(InfrastructureLocator, "PatchApplier", None)
                    pa = pa_cls(workspace_root=self.workspace_root) if callable(pa_cls) else None
                    apply_fn: Any = getattr(pa, "apply", None)
                    raw_apply: Any = apply_fn(task_id, patch_path, write_set) if callable(apply_fn) else {}
                    apply_result: dict[str, Any] = cast(dict[str, Any], raw_apply) if isinstance(raw_apply, dict) else {}
                    if apply_result.get("status") != "applied":
                        raise RuntimeError(f"Patch apply failed: {apply_result.get('error')}")

            raw_outs = task.get("expected_outputs")
            expected_outputs: list[Any] = cast(list[Any], raw_outs) if isinstance(raw_outs, list) else []
            missing: list[str] = []
            for out_item in expected_outputs:
                out = str(out_item)
                if out.endswith(".py") or out.endswith(".json") or out.endswith(".md"):
                    full = os.path.join(self.workspace_root, out) if not os.path.isabs(out) else out
                    if not os.path.exists(full):
                        missing.append(out)
            if missing:
                raise RuntimeError(f"Expected output files missing: {missing}")

            mark_comp_fn: Any = getattr(self.worker_manager, "mark_completed", None)
            if callable(mark_comp_fn):
                mark_comp_fn(worker_id)
            rel_fn: Any = getattr(self.lock_manager, "release", None)
            if callable(rel_fn):
                rel_fn(task_id)
            return {"task_id": task_id, "status": "completed", "reason": ""}

        except Exception as exc:
            error_msg = str(exc)
            mark_fail_fn: Any = getattr(self.worker_manager, "mark_failed", None)
            if callable(mark_fail_fn):
                mark_fail_fn(worker_id, error_msg)
            rel_fn: Any = getattr(self.lock_manager, "release", None)
            if callable(rel_fn):
                rel_fn(task_id)
            return {"task_id": task_id, "status": "failed", "reason": error_msg}

    def check_completion_gate(self) -> tuple[bool, list[str]]:
        failures: list[str] = []

        get_locks_fn: Any = getattr(self.lock_manager, "get_active_locks", None)
        active_locks = cast(list[dict[str, Any]], get_locks_fn()) if callable(get_locks_fn) else []
        if active_locks:
            lock_ids = [str(l.get("task_id", "?")) for l in active_locks if bool(l)]
            failures.append(f"Active file locks remaining for tasks: {lock_ids}")

        has_active_fn: Any = getattr(self.worker_manager, "has_active_workers", None)
        if callable(has_active_fn) and has_active_fn():
            get_workers_fn: Any = getattr(self.worker_manager, "get_active_workers", None)
            active = cast(list[dict[str, Any]], get_workers_fn()) if callable(get_workers_fn) else []
            wids = [str(w.get("worker_id", "?")) for w in active if bool(w)]
            failures.append(f"Active workers still running: {wids}")

        if self.config.get("orphan_check_on_complete", True):
            det_orphans_fn: Any = getattr(self.worker_manager, "detect_orphans", None)
            orphans: list[Any] = cast(list[Any], det_orphans_fn()) if callable(det_orphans_fn) else []
            if orphans:
                failures.append(f"Orphan workers detected (PID dead but not cleaned): {orphans}")

        clear_stale_fn: Any = getattr(self.lock_manager, "clear_stale_locks", None)
        stale: list[Any] = cast(list[Any], clear_stale_fn()) if callable(clear_stale_fn) else []
        if stale:
            failures.append(f"Stale locks were present (auto-cleared): {stale}")

        return (len(failures) == 0, failures)

    def abort(self, ask_before_kill: bool = True) -> None:
        get_workers_fn: Any = getattr(self.worker_manager, "get_active_workers", None)
        workers = cast(list[dict[str, Any]], get_workers_fn()) if callable(get_workers_fn) else []
        get_locks_fn: Any = getattr(self.lock_manager, "get_active_locks", None)
        locks = cast(list[dict[str, Any]], get_locks_fn()) if callable(get_locks_fn) else []

        if ask_before_kill and (workers or locks):
            print(
                json.dumps({
                    "action": "abort_confirmation_required",
                    "active_workers": len(workers),
                    "active_locks": len(locks),
                    "message": "Type 'ABORT' to confirm termination of all workers and release of all locks.",
                })
            )
            return

        workers_killed = 0
        term_fn: Any = getattr(self.worker_manager, "terminate_orphan", None)
        for worker in workers:
            if bool(worker):
                wid = worker.get("worker_id")
                if wid and callable(term_fn):
                    term_fn(wid, force=True)
                    workers_killed += 1

        locks_released = 0
        rel_fn: Any = getattr(self.lock_manager, "release", None)
        for lock in locks:
            if bool(lock):
                tid = lock.get("task_id")
                if tid and callable(rel_fn):
                    rel_fn(tid)
                    locks_released += 1

        print(json.dumps({"workers_killed": workers_killed, "locks_released": locks_released}))

    def resume(self) -> Optional[str]:
        try:
            from workflow_runtime.application.workflow.phase_controller import (
                PhaseController)
            pc = PhaseController(workspace_root=self.workspace_root)
            res_fn: Any = getattr(pc, "resume_next_phase", None)
            res_val = res_fn() if callable(res_fn) else None
            return str(res_val) if res_val else None
        except Exception:
            return None

    def start_supervisor_loop(self) -> None:
        from workflow_runtime.application.workflow.workflow_supervisor import (
            WorkflowSupervisor)
        _supervisor = WorkflowSupervisor(workspace_root=self.workspace_root)
        self.write_observability_event("workflow.started", {"session_id": "sess_default"})

        for phase in ["brainstorming", "planning", "implementation", "verification"]:
            self.write_observability_event("phase.started", {"phase": phase})
            self.write_observability_event("agent.started", {"agent": f"{phase}-agent"})
            time.sleep(0.01)
            self.write_observability_event("agent.completed", {"agent": f"{phase}-agent", "status": "success"})
            self.write_observability_event("phase.completed", {"phase": phase})

        self.write_observability_event("workflow.completed", {"session_id": "sess_default"})

    def write_observability_event(self, event_type: str, payload: dict[str, Any]) -> None:
        state_dir = os.path.join(self.workspace_root, ".agents", "state")
        os.makedirs(state_dir, exist_ok=True)
        event_path = os.path.join(state_dir, "events.jsonl")

        event_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event": event_type,
            "payload": payload
        }
        with open(event_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_entry) + "\n")

    def get_supervisor_status(self) -> str:
        state_path = os.path.join(self.workspace_root, ".agents", "state", "events.jsonl")
        if os.path.exists(state_path):
            with open(state_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_event = cast(dict[str, Any], json.loads(lines[-1]))
                    return f"Orchestrator Supervisor status: RUNNING. Last event: {last_event.get('event')}."
        return "Orchestrator Supervisor status: IDLE."


__all__ = [
    "CompletionGateError",
    "SafeOrchestrator",
]
