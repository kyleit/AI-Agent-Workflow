from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, cast

from workflow_runtime.application.use_cases.process_execution_runner import (
    ProcessExecutionRunner)
from workflow_runtime.application.use_cases.process_registry import (
    LOGS_DIR, REGISTRY_PATH, ProcessRegistry)


class ExecutionManager(ProcessExecutionRunner):
    _scheduler_thread: Optional[threading.Thread] = None
    _scheduler_stop = threading.Event()

    @staticmethod
    def start_scheduler() -> None:
        if ExecutionManager._scheduler_thread is None:
            ExecutionManager._scheduler_stop.clear()
            ExecutionManager._scheduler_thread = threading.Thread(
                target=ExecutionManager._scheduler_loop, daemon=True
            )
            ExecutionManager._scheduler_thread.start()

    @staticmethod
    def stop_scheduler() -> None:
        ExecutionManager._scheduler_stop.set()
        if ExecutionManager._scheduler_thread:
            ExecutionManager._scheduler_thread.join(timeout=2)
            ExecutionManager._scheduler_thread = None

    @staticmethod
    def _scheduler_loop() -> None:
        while not ExecutionManager._scheduler_stop.wait(1.0):
            try:
                ExecutionManager.tick_scheduler()
            except Exception as e:
                print(f"[ExecutionManager] Scheduler error: {e}", file=sys.stderr)

    @staticmethod
    def get_system_capacity() -> Tuple[int, int, int]:
        cpu_count = os.cpu_count() or 1
        total_memory = 8 * 1024 * 1024 * 1024
        available_memory = 4 * 1024 * 1024 * 1024
        try:
            import psutil
            vm = psutil.virtual_memory()
            total_memory = vm.total
            available_memory = vm.available
        except ImportError:
            if os.path.exists("/proc/meminfo"):
                try:
                    with open("/proc/meminfo", "r") as f:
                        for line in f:
                            if line.startswith("MemAvailable:"):
                                available_memory = int(line.split()[1]) * 1024
                            elif line.startswith("MemTotal:"):
                                total_memory = int(line.split()[1]) * 1024
                except Exception:
                    pass
        return cpu_count, total_memory, available_memory

    @staticmethod
    def validate_request(req: Dict[str, Any]) -> Tuple[bool, str]:
        session_path = os.path.abspath(os.path.join(".", ".agents", ".session.json"))
        session_data: dict[str, Any] = {}
        if os.path.exists(session_path):
            try:
                with open(session_path, "r", encoding="utf-8") as f:
                    raw_sd = json.load(f)
                    if isinstance(raw_sd, dict):
                        session_data = cast(dict[str, Any], raw_sd)
            except Exception:
                pass

        execution_mode = str(os.environ.get("AIWF_EXECUTION_MODE") or session_data.get("execution_mode") or "")
        workflow_id = str(os.environ.get("AIWF_WORKFLOW_ID") or session_data.get("workflow_id") or "")

        is_testing = os.environ.get("AIWF_TESTING") == "true"
        if not is_testing and (execution_mode != "workflow" or not workflow_id):
            return False, "EXECUTION_BLOCKED: Engineering action outside Workflow Gateway."

        cwd = str(req.get("working_directory", "."))
        abs_cwd = os.path.abspath(cwd)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))

        is_testing_override = is_testing or os.environ.get("AIWF_STRICT_PROCESS_ENFORCEMENT") == "true" or "pytest" in abs_cwd.lower()
        if not is_testing_override and not abs_cwd.startswith(repo_root):
            return False, f"Working directory {cwd} is outside workspace bounds."

        owner = str(req.get("owner_agent_id", ""))
        cmd = str(req.get("command", ""))
        args: list[Any] = cast(list[Any], req.get("arguments", [])) if isinstance(req.get("arguments"), list) else []
        cmd_str = " ".join([cmd] + [str(a) for a in args]).lower()

        is_test = False
        test_execs = ["pytest", "unittest", "vitest", "jest", "playwright", "cypress", "npm test", "npm run test", "go test"]
        for te in test_execs:
            if te in cmd_str:
                is_test = True
                break
        if "test_" in cmd_str or "test.py" in cmd_str:
            is_test = True

        if is_test:
            is_tester = "tester" in owner.lower() or "qa" in owner.lower() or owner == "AGENT-TESTER-001"
            if not is_tester:
                return False, f"Test commands must be owned by a TESTER or QA Agent. (Owner: {owner})"

        is_release = False
        release_keywords = ["git push", "git tag", "publish", "deploy", "release"]
        for rk in release_keywords:
            if rk in cmd_str:
                is_release = True
                break
        if is_release:
            is_release_agent = "release" in owner.lower() or owner == "AGENT-RELEASE-001"
            if not is_release_agent:
                return False, f"Release/deployment commands must be owned by a Release Agent. (Owner: {owner})"

        return True, "Valid request"

    @staticmethod
    def submit(req: Dict[str, Any]) -> str:
        execution_id = f"EXEC-{int(time.time() * 1000)}"

        item = {
            "execution_id": execution_id,
            "workflow_id": req.get("workflow_id") or os.environ.get("AIWF_WORKFLOW_ID") or "WF-N/A",
            "task_id": req.get("task_id", "TASK-N/A"),
            "owner_agent_id": req.get("owner_agent_id", "AGENT-UNKNOWN"),
            "command": req.get("command", ""),
            "arguments": req.get("arguments", []),
            "working_directory": req.get("working_directory", "."),
            "status": "CREATED",
            "priority": req.get("priority", "normal"),
            "is_force_task": req.get("is_force_task", False),
            "created_at": datetime.now().astimezone().isoformat(),
            "started_at": None,
            "last_heartbeat_at": None,
            "completed_at": None,
            "timeout_seconds": req.get("timeout", None) or req.get("timeout_seconds", 300),
            "cancel_requested_at": None,
            "exit_code": None,
            "termination_reason": None,
            "cpu_limit": req.get("cpu_limit", 1.0),
            "memory_limit": req.get("memory_limit", 0.5),
            "observed_cpu": 0.0,
            "observed_memory": 0.0,
            "stdout_artifact": os.path.join(LOGS_DIR, f"{execution_id}.stdout"),
            "stderr_artifact": os.path.join(LOGS_DIR, f"{execution_id}.stderr"),
            "result_artifact": None,
            "retry_count": req.get("retry_count", 0),
            "stdin_mode": req.get("stdin_mode", "disabled"),
            "pid": None,
            "process_group_id": None
        }

        valid, msg = ExecutionManager.validate_request(item)
        if not valid:
            raise PermissionError(f"Command execution request rejected: {msg}")

        data = ProcessRegistry.read()
        data[execution_id] = item
        ProcessRegistry.write(data)

        ExecutionManager._transition(execution_id, "QUEUED")
        return execution_id

    @staticmethod
    def _transition(execution_id: str, new_status: str, extra: Dict[str, Any] | None = None) -> None:
        valid_transitions = {
            "CREATED": ["QUEUED", "FAILED"],
            "QUEUED": ["STARTING", "FAILED", "CANCELLING", "CANCELLED"],
            "STARTING": ["RUNNING", "FAILED", "CANCELLING", "CANCELLED"],
            "RUNNING": ["PAUSING", "CANCELLING", "COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED", "BLOCKED_INTERACTIVE"],
            "PAUSING": ["PAUSED", "FAILED", "CANCELLING"],
            "PAUSED": ["RESUMING", "CANCELLING"],
            "RESUMING": ["RUNNING", "FAILED", "CANCELLING"],
            "CANCELLING": ["TERMINATING", "CANCELLED", "FAILED"],
            "TERMINATING": ["CANCELLED", "FAILED"],
            "COMPLETED": [],
            "FAILED": [],
            "CANCELLED": [],
            "TIMED_OUT": [],
            "ORPHANED": [],
            "BLOCKED_INTERACTIVE": []
        }

        data = ProcessRegistry.read()
        item = cast(Dict[str, Any], data.get(execution_id)) if isinstance(data.get(execution_id), dict) else {}
        if not item or "status" not in item:
            return

        current = str(item["status"])
        if new_status not in valid_transitions.get(current, []) and new_status != "ORPHANED" and new_status != "BLOCKED_INTERACTIVE":
            if new_status not in ["ORPHANED", "FAILED", "CANCELLED", "TIMED_OUT"]:
                raise ValueError(f"Invalid state transition from {current} to {new_status}")

        updates: dict[str, Any] = {"status": new_status}
        if extra:
            updates.update(extra)

        now_str = datetime.now().astimezone().isoformat()
        if new_status == "RUNNING" and not item.get("started_at"):
            updates["started_at"] = now_str
        if new_status in ["COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "ORPHANED", "BLOCKED_INTERACTIVE"]:
            updates["completed_at"] = now_str

        ProcessRegistry.update(execution_id, updates)

    @staticmethod
    def tick_scheduler() -> None:
        data = ProcessRegistry.read()
        queued: list[dict[str, Any]] = [
            cast(dict[str, Any], v) for v in data.values()
            if isinstance(v, dict) and str(cast(dict[str, Any], v).get("status", "")) == "QUEUED"
        ]
        if not queued:
            return

        def sort_key(x: dict[str, Any]) -> tuple[int, str]:
            priority_val = 0
            if bool(x.get("is_force_task")):
                priority_val = 100
            elif str(x.get("priority", "")) == "high":
                priority_val = 10
            elif str(x.get("priority", "")) == "low":
                priority_val = -10
            return (-priority_val, str(x.get("created_at", "")))

        queued.sort(key=sort_key)

        running: list[dict[str, Any]] = [
            cast(dict[str, Any], v) for v in data.values()
            if isinstance(v, dict) and str(cast(dict[str, Any], v).get("status", "")) in ["STARTING", "RUNNING", "PAUSED", "PAUSING", "RESUMING"]
        ]
        cpu_count, _total_mem, _avail_mem = ExecutionManager.get_system_capacity()
        active_cpu_load = sum(float(str(v.get("cpu_limit", 1.0))) for v in running)

        for item in queued:
            req_cpu = float(str(item.get("cpu_limit", 1.0)))
            if active_cpu_load + req_cpu > cpu_count and not bool(item.get("is_force_task")):
                continue

            try:
                ExecutionManager._start_process(str(item["execution_id"]))
                active_cpu_load += req_cpu
            except Exception as e:
                ExecutionManager._transition(str(item["execution_id"]), "FAILED", {
                    "termination_reason": f"Failed to spawn process: {e}"
                })

    @staticmethod
    def _placeholder() -> None:
        pass


__all__ = [
    "ProcessRegistry",
    "ExecutionManager",
]
