"""
workflow_runtime/application/use_cases/process_execution_runner.py

Process lifecycle monitor, starter, and cancellation runner for background processes.
"""
from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, cast

from workflow_runtime.application.use_cases.process_registry import (
    ProcessRegistry)

LOGS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../../../.agents/runtime/logs"
))
os.makedirs(LOGS_DIR, exist_ok=True)


class ProcessExecutionRunner:
    """Runner mixin providing process lifecycle control: start, monitor, kill, cancel, pause, resume."""

    @classmethod
    def _start_process(cls, execution_id: str) -> None:
        data = ProcessRegistry.read()
        item = cast(dict[str, Any], data.get(execution_id)) if isinstance(data.get(execution_id), dict) else {}
        if not item:
            return

        from workflow_runtime.application.use_cases.execution_manager import (
            ExecutionManager)
        transition_fn: Any = getattr(ExecutionManager, "_transition", None)
        if callable(transition_fn):
            transition_fn(execution_id, "STARTING")

        cmd = str(item.get("command", ""))
        raw_args = item.get("arguments", [])
        args = [str(a) for a in cast(list[Any], raw_args)] if isinstance(raw_args, list) else []
        cwd_val = item.get("working_directory")
        cwd = str(cwd_val) if cwd_val is not None else None
        stdin_mode = str(item.get("stdin_mode", ""))

        cmd_list = [cmd] + args

        stdin_val = subprocess.DEVNULL
        if stdin_mode == "managed":
            stdin_val = subprocess.PIPE

        preexec = None
        creationflags = 0
        if os.name != 'nt':
            preexec = getattr(os, "setsid", None)
        else:
            creationflags = 0x00000200

        proc = subprocess.Popen(
            cmd_list,
            cwd=cwd,
            stdin=stdin_val,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=preexec,
            creationflags=creationflags,
            text=True
        )

        pgid = proc.pid
        if os.name != 'nt':
            try:
                getpgid_fn: Any = getattr(os, "getpgid", None)
                if callable(getpgid_fn):
                    pgid = int(cast(int, getpgid_fn(proc.pid)))
            except Exception:
                pgid = proc.pid

        if callable(transition_fn):
            transition_fn(execution_id, "RUNNING", {
                "pid": proc.pid,
                "process_group_id": pgid,
                "last_heartbeat_at": datetime.now().astimezone().isoformat()
            })

        monitor = threading.Thread(
            target=cls._monitor_process_lifecycle,
            args=(execution_id, proc),
            daemon=True
        )
        monitor.start()

    @staticmethod
    def _monitor_process_lifecycle(execution_id: str, proc: subprocess.Popen[str]) -> None:
        data = ProcessRegistry.read()
        item = cast(dict[str, Any], data.get(execution_id)) if isinstance(data.get(execution_id), dict) else {}
        if not item or "status" not in item:
            return

        timeout = float(item.get("timeout_seconds", 300))
        start_time = time.time()

        is_blocked = [False]
        blocked_reason = [""]

        def read_stdout() -> None:
            try:
                stdout_path = str(item.get("stdout_artifact", ""))
                with open(stdout_path, "w", encoding="utf-8") as f:
                    if proc.stdout is not None:
                        for line in proc.stdout:
                            f.write(line)
                            f.flush()

                            if item.get("stdin_mode") == "disabled":
                                content = line.lower()
                                keywords = ["confirm", "[y/n]", "enter your password", "password:", "approve?", "proceed?"]
                                for kw in keywords:
                                    if kw in content:
                                        is_blocked[0] = True
                                        blocked_reason[0] = f"Process blocked waiting for stdin prompt: '{kw}'"
                                        try:
                                            if os.name != 'nt':
                                                killpg_fn: Any = getattr(os, "killpg", None)
                                                if callable(killpg_fn):
                                                    pgid_val = int(cast(int, item.get("process_group_id") or proc.pid))
                                                    killpg_fn(pgid_val, signal.SIGKILL)
                                            else:
                                                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                                        except Exception:
                                            pass
                                        return
            except Exception:
                pass

        def read_stderr() -> None:
            try:
                stderr_path = str(item.get("stderr_artifact", ""))
                with open(stderr_path, "w", encoding="utf-8") as f:
                    if proc.stderr is not None:
                        for line in proc.stderr:
                            f.write(line)
                            f.flush()
            except Exception:
                pass

        t_out = threading.Thread(target=read_stdout, daemon=True)
        t_err = threading.Thread(target=read_stderr, daemon=True)
        t_out.start()
        t_err.start()

        from workflow_runtime.application.use_cases.execution_manager import (
            ExecutionManager)
        transition_fn: Any = getattr(ExecutionManager, "_transition", None)

        while True:
            exit_code = proc.poll()
            if exit_code is not None:
                t_out.join(timeout=0.2)
                t_err.join(timeout=0.2)

                status = "COMPLETED" if exit_code == 0 else "FAILED"
                reason: str | None = None

                if is_blocked[0]:
                    status = "BLOCKED_INTERACTIVE"
                    reason = blocked_reason[0]
                else:
                    updated_data = ProcessRegistry.read()
                    updated_item = cast(dict[str, Any], updated_data.get(execution_id)) if isinstance(updated_data.get(execution_id), dict) else {}
                    if updated_item and updated_item.get("status") in ["CANCELLING", "TERMINATING", "CANCELLED"]:
                        status = "CANCELLED"
                        reason = str(updated_item.get("termination_reason", ""))

                if callable(transition_fn):
                    transition_fn(execution_id, status, {
                        "exit_code": exit_code,
                        "termination_reason": reason,
                        "completed_at": datetime.now().astimezone().isoformat()
                    })
                break

            elapsed = time.time() - start_time
            if timeout and elapsed > timeout:
                try:
                    if os.name != 'nt':
                        killpg_fn: Any = getattr(os, "killpg", None)
                        if callable(killpg_fn):
                            pgid_val = int(cast(int, item.get("process_group_id") or proc.pid))
                            killpg_fn(pgid_val, signal.SIGKILL)
                    else:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                except Exception:
                    pass
                if callable(transition_fn):
                    transition_fn(execution_id, "TIMED_OUT", {
                        "termination_reason": f"Execution timed out after {timeout} seconds."
                    })
                break

            try:
                now_str = datetime.now().astimezone().isoformat()
                updates: dict[str, Any] = {"last_heartbeat_at": now_str}
                try:
                    import psutil
                    p = psutil.Process(proc.pid)
                    updates["observed_cpu"] = p.cpu_percent(interval=0.1)
                    updates["observed_memory"] = p.memory_info().rss / (1024 * 1024)
                except Exception:
                    pass
                ProcessRegistry.update(execution_id, updates)
            except Exception:
                pass

            time.sleep(0.5)

    @staticmethod
    def cancel(execution_id: str, reason: str = "CANCELLED") -> None:
        data = ProcessRegistry.read()
        item = cast(dict[str, Any], data.get(execution_id)) if isinstance(data.get(execution_id), dict) else {}
        if not item or item.get("status") in ["COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "ORPHANED", "BLOCKED_INTERACTIVE"]:
            return

        from workflow_runtime.application.use_cases.execution_manager import (
            ExecutionManager)
        transition_fn: Any = getattr(ExecutionManager, "_transition", None)
        if callable(transition_fn):
            transition_fn(execution_id, "CANCELLING", {
                "cancel_requested_at": datetime.now().astimezone().isoformat(),
                "termination_reason": reason
            })

        raw_pid = item.get("pid")
        raw_pgid = item.get("process_group_id")
        if not raw_pid:
            if callable(transition_fn):
                transition_fn(execution_id, "CANCELLED")
            return

        pid = int(cast(int, raw_pid))
        pgid = int(cast(int, raw_pgid)) if raw_pgid is not None else pid

        if os.name != 'nt':
            try:
                killpg_fn: Any = getattr(os, "killpg", None)
                if callable(killpg_fn):
                    killpg_fn(pgid, signal.SIGTERM)
            except Exception:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
        else:
            try:
                ctrl_c = getattr(signal, "CTRL_C_EVENT", 0)
                os.kill(pid, ctrl_c)
            except Exception:
                pass

        time.sleep(1.0)

        is_alive_fn: Any = getattr(ExecutionManager, "is_pid_alive", None)
        kill_fn: Any = getattr(ExecutionManager, "kill", None)
        if callable(is_alive_fn) and bool(is_alive_fn(pid)):
            if callable(kill_fn):
                kill_fn(execution_id, reason)
        else:
            if callable(transition_fn):
                transition_fn(execution_id, "CANCELLED")

    @staticmethod
    def kill(execution_id: str, reason: str = "KILLED") -> None:
        data = ProcessRegistry.read()
        item = cast(dict[str, Any], data.get(execution_id)) if isinstance(data.get(execution_id), dict) else {}
        if not item:
            return

        pid = item.get("pid")
        pgid = item.get("process_group_id")
        if not pid:
            return

        if os.name != 'nt':
            try:
                os.killpg(int(cast(int, pgid or pid)), signal.SIGKILL)
            except Exception:
                try:
                    os.kill(int(cast(int, pid)), signal.SIGKILL)
                except Exception:
                    pass
        else:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            except Exception:
                try:
                    os.kill(int(cast(int, pid)), signal.SIGABRT)
                except Exception:
                    pass

        from workflow_runtime.application.use_cases.execution_manager import (
            ExecutionManager)
        transition_fn: Any = getattr(ExecutionManager, "_transition", None)
        if callable(transition_fn):
            transition_fn(execution_id, "CANCELLED", {"termination_reason": reason})

    @staticmethod
    def pause(execution_id: str) -> None:
        data = ProcessRegistry.read()
        item = cast(dict[str, Any], data.get(execution_id)) if isinstance(data.get(execution_id), dict) else {}
        if not item or item.get("status") != "RUNNING":
            return

        from workflow_runtime.application.use_cases.execution_manager import (
            ExecutionManager)
        transition_fn: Any = getattr(ExecutionManager, "_transition", None)
        if callable(transition_fn):
            transition_fn(execution_id, "PAUSING")

        pid = item.get("pid")
        pgid = item.get("process_group_id")
        if not pid:
            return

        if os.name != 'nt':
            try:
                os.killpg(int(cast(int, pgid or pid)), signal.SIGSTOP)
                if callable(transition_fn):
                    transition_fn(execution_id, "PAUSED")
            except Exception as e:
                if callable(transition_fn):
                    transition_fn(execution_id, "RUNNING")
                raise RuntimeError(f"PAUSE_UNSUPPORTED: SIGSTOP failed. {e}")
        else:
            if callable(transition_fn):
                transition_fn(execution_id, "RUNNING")
            raise RuntimeError("PAUSE_UNSUPPORTED: Windows does not natively support SIGSTOP.")

    @staticmethod
    def resume(execution_id: str) -> None:
        data = ProcessRegistry.read()
        item = cast(dict[str, Any], data.get(execution_id)) if isinstance(data.get(execution_id), dict) else {}
        if not item or item.get("status") != "PAUSED":
            return

        pid = item.get("pid")
        pgid = item.get("process_group_id")
        if not pid:
            return

        from workflow_runtime.application.use_cases.execution_manager import (
            ExecutionManager)
        transition_fn: Any = getattr(ExecutionManager, "_transition", None)

        if os.name != 'nt':
            try:
                os.killpg(int(cast(int, pgid or pid)), signal.SIGCONT)
                if callable(transition_fn):
                    transition_fn(execution_id, "RUNNING")
            except Exception as e:
                raise RuntimeError(f"RESUME_FAILED: {e}")
        else:
            raise RuntimeError("RESUME_UNSUPPORTED: Windows does not support SIGCONT.")

    @staticmethod
    def recover() -> int:
        data = ProcessRegistry.read()
        recovered = 0
        for eid, item_raw in data.items():
            if isinstance(item_raw, dict):
                item = cast(dict[str, Any], item_raw)
                status = item.get("status")
                pid = item.get("pid")
                if status in ["RUNNING", "STARTING"] and pid:
                    from workflow_runtime.application.use_cases.execution_manager import (
                        ExecutionManager)
                    is_alive_fn: Any = getattr(ExecutionManager, "is_pid_alive", None)
                    alive = bool(is_alive_fn(int(cast(int, pid)))) if callable(is_alive_fn) else False
                    if not alive:
                        transition_fn: Any = getattr(ExecutionManager, "_transition", None)
                        if callable(transition_fn):
                            transition_fn(eid, "ORPHANED", {"termination_reason": "Process died unexpectedly."})
                        recovered += 1
        return recovered

    @staticmethod
    def get_system_capacity() -> tuple[int, int, int]:
        try:
            import psutil
            vm = psutil.virtual_memory()
            return psutil.cpu_count() or 1, vm.total, vm.available
        except Exception:
            return 1, 8 * 1024 * 1024 * 1024, 4 * 1024 * 1024 * 1024


__all__ = ["ProcessExecutionRunner"]
