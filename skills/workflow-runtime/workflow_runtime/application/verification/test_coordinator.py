from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
import uuid
from datetime import datetime
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator

from workflow_runtime.application.verification.test_session_coordinator import (
    TestSessionCoordinator)


class TestCoordinator(TestSessionCoordinator):
    def __init__(self, workspace_path: str = "."):
        self.workspace_root = os.path.abspath(workspace_path)
        self.state_dir = os.path.join(self.workspace_root, ".agents", "state")
        self.lock_path = os.path.join(self.state_dir, "pytest_coordinator.lock")
        self.exec_path = os.path.join(self.state_dir, "test-coordinator.json")
        os.makedirs(self.state_dir, exist_ok=True)
        self.git_rev: str = "unknown"

    def _load_coordinator_state(self) -> dict[str, Any]:
        if os.path.exists(self.exec_path):
            try:
                with open(self.exec_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return cast(dict[str, Any], data)
            except Exception:
                pass
        return {"active_runs": [], "queue": []}

    def _save_coordinator_state(self, state: dict[str, Any]) -> None:
        try:
            with open(self.exec_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def check_rate_limit(self) -> tuple[bool, str]:
        now = time.time()
        cb_path = os.path.join(self.state_dir, "circuit-breakers.json")
        cb_data: dict[str, Any] = {
            "pytest_circuit": "closed",
            "updated_at": datetime.now().astimezone().isoformat()
        }
        if os.path.exists(cb_path):
            try:
                with open(cb_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        cb_data.update(cast(dict[str, Any], loaded))
            except Exception:
                pass

        if cb_data.get("pytest_circuit") == "open":
            return False, "pytest circuit breaker is OPEN"

        history_path = os.path.join(self.state_dir, "pytest_history.json")
        history: list[dict[str, Any]] = []
        if os.path.exists(history_path):
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    h_data = json.load(f)
                    if isinstance(h_data, list):
                        history = cast(list[dict[str, Any]], h_data)
            except Exception:
                pass

        window = 300
        recent = [h for h in history if now - float(cast(float, h.get("timestamp", 0.0))) < window]
        if len(recent) > 30:
            return False, f"Rate limit exceeded: {len(recent)} runs in last 5m (max 30)"

        return True, "OK"

    def get_resource_metrics(self) -> dict[str, Any]:
        import psutil
        try:
            cpu = float(psutil.cpu_percent(interval=None))
            ram = float(psutil.virtual_memory().percent)
        except Exception:
            cpu = 0.0
            ram = 0.0
        return {"cpu": cpu, "ram": ram}

    def check_resources_ok(self, policy: dict[str, Any] | None = None) -> tuple[bool, str]:
        metrics = self.get_resource_metrics()
        pol_dict = policy or {}

        limits: dict[str, Any] = cast(dict[str, Any], pol_dict.get("resource_limits", {})) if isinstance(pol_dict.get("resource_limits"), dict) else {}
        cpu_limit = float(limits.get("cpu_throttle_percent", 80))
        ram_limit = float(limits.get("memory_throttle_percent", 80))

        if metrics["cpu"] > cpu_limit:
            return False, f"CPU usage is {metrics['cpu']}% (limit: {cpu_limit}%)"
        if metrics["ram"] > ram_limit:
            return False, f"RAM usage is {metrics['ram']}% (limit: {ram_limit}%)"

        return True, "OK"

    def run_coordinated(self, cmd: list[str], test_mode: str, test_scope: str, force: bool = False) -> tuple[int, str, str]:
        policy: dict[str, Any] = cast(dict[str, Any], getattr(InfrastructureLocator, "load_runtime_policy")(validate=True))
        te_cfg: dict[str, Any] = cast(dict[str, Any], policy.get("test_execution", {})) if isinstance(policy.get("test_execution"), dict) else {}

        # 1. Deduplication key
        session: dict[str, Any] = cast(dict[str, Any], getattr(InfrastructureLocator, "load_session")())
        project_id = str(session.get("project_id", "ai-skill-framework"))
        work_item_raw = session.get("work_item")
        if isinstance(work_item_raw, dict):
            work_item_dict = cast(dict[str, Any], work_item_raw)
            work_item_id = str(work_item_dict.get("id", "default_work_item"))
        else:
            work_item_id = str(work_item_raw or os.environ.get("AIWF_WORK_ITEM_ID", "default_work_item"))

        # Git revision
        git_rev = "unknown"
        try:
            git_rev = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            pass
        self.git_rev = git_rev

        # Changed files hash
        from workflow_runtime.application.analysis.tia_engine import \
            TestImpactResolver
        resolver = TestImpactResolver()
        changed_raw = getattr(resolver, "get_git_changed_files")()
        changed = sorted(cast(list[str], changed_raw))
        changed_hash = hashlib.sha256(json.dumps(changed).encode()).hexdigest()[:16]

        dedup_raw = f"{project_id}:{work_item_id}:{test_mode}:{test_scope}:{git_rev}:{changed_hash}"
        dedup_key = hashlib.sha256(dedup_raw.encode("utf-8")).hexdigest()[:16]

        outcome_path = os.path.join(self.state_dir, f"test_outcome_{dedup_key}.json")

        # Check if identical successful run has already completed and outcome cache is valid
        if not force and os.path.exists(outcome_path):
            try:
                with open(outcome_path, "r", encoding="utf-8") as f:
                    cached = cast(dict[str, Any], json.load(f))
                if cached.get("status") == "success":
                    print(f"[INFO] Reusing cached successful test result for dedup_key {dedup_key}.")
                    return int(cached.get("returncode", 0)), str(cached.get("stdout", "")), str(cached.get("stderr", ""))
            except Exception:
                pass

        run_id = f"run_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        caller_pid = os.getpid()

        # 2. Acquire lock to modify state
        lock: Any = getattr(InfrastructureLocator, "OSFileLock")(self.lock_path)
        while not lock.acquire():
            time.sleep(0.1)

        try:
            state = self._load_coordinator_state()

            # Check duplicate active run
            dedup_enabled = bool(te_cfg.get("deduplicate_requests", True))
            if dedup_enabled:
                for run in cast(list[dict[str, Any]], state.get("active_runs", [])):
                    if run.get("dedup_key") == dedup_key:
                        # Join as subscriber
                        subs: list[int] = cast(list[int], run.get("subscribers", []))
                        subs.append(caller_pid)
                        run["subscribers"] = subs
                        self._save_coordinator_state(state)
                        lock.release()

                        active_pid = cast(int, run.get("pid", 0))
                        print(f"[INFO] Subscribed to existing test run {run.get('run_id')}. Waiting for coalesced results...")
                        return self._wait_for_outcome(str(run.get("run_id")), outcome_path, active_pid)

            # Not duplicate or dedup disabled: check process limit & resource limits
            max_parallel = int(te_cfg.get("max_parallel_pytest_processes", 1))

            # Clean up dead active runs first
            active_runs: list[dict[str, Any]] = []
            for run in cast(list[dict[str, Any]], state.get("active_runs", [])):
                run_pid = cast(int, run.get("pid", -1))
                is_alive_fn: Any = getattr(InfrastructureLocator, "is_process_alive", None)
                if callable(is_alive_fn) and is_alive_fn(run_pid):
                    active_runs.append(run)
            state["active_runs"] = active_runs

            resources_ok, res_msg = self.check_resources_ok(policy)

            should_queue = len(active_runs) >= max_parallel or (not resources_ok and not force)

            if should_queue:
                queue_item: dict[str, Any] = {
                    "run_id": run_id,
                    "pid": caller_pid,
                    "dedup_key": dedup_key,
                    "cmd": cmd,
                    "test_mode": test_mode,
                    "test_scope": test_scope,
                    "queued_at": datetime.now().astimezone().isoformat()
                }
                queue_list: list[dict[str, Any]] = cast(list[dict[str, Any]], state.get("queue", []))
                queue_list.append(queue_item)
                state["queue"] = queue_list
                self._save_coordinator_state(state)
                lock.release()

                print(f"[INFO] Test run {run_id} queued. Reason: " + ("Max process limit reached" if len(active_runs) >= max_parallel else res_msg))
                return self._wait_in_queue(run_id, dedup_key, outcome_path)

            # Start running immediately
            new_run: dict[str, Any] = {
                "run_id": run_id,
                "pid": caller_pid,
                "dedup_key": dedup_key,
                "cmd": cmd,
                "test_mode": test_mode,
                "test_scope": test_scope,
                "subscribers": [caller_pid],
                "started_at": datetime.now().astimezone().isoformat()
            }
            active_runs.append(new_run)
            state["active_runs"] = active_runs
            self._save_coordinator_state(state)
        finally:
            if getattr(lock, "is_held", False):
                lock.release()

        # 3. Execute test run
        return self._execute_pytest(run_id, cmd, dedup_key, outcome_path, te_cfg, test_mode)


__all__ = ["TestCoordinator"]
