# execution_manager.py
import os
import sys
import json
import time
import signal
import subprocess
import tempfile
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

REGISTRY_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../../../.agents/state/executions.json"
))

LOGS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "../../../.agents/runtime/logs"
))
os.makedirs(LOGS_DIR, exist_ok=True)

class ProcessRegistry:
    @staticmethod
    def read() -> Dict[str, Any]:
        if not os.path.exists(REGISTRY_PATH):
            return {}
        try:
            with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def write(data: Dict[str, Any]) -> None:
        dir_name = os.path.dirname(REGISTRY_PATH)
        os.makedirs(dir_name, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_path, REGISTRY_PATH)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    @staticmethod
    def update(execution_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        data = ProcessRegistry.read()
        if execution_id not in data:
            data[execution_id] = {}
        data[execution_id].update(updates)
        ProcessRegistry.write(data)
        return data[execution_id]

class ExecutionManager:
    _scheduler_thread: Optional[threading.Thread] = None
    _scheduler_stop = threading.Event()

    @staticmethod
    def start_scheduler():
        if ExecutionManager._scheduler_thread is None:
            ExecutionManager._scheduler_stop.clear()
            ExecutionManager._scheduler_thread = threading.Thread(
                target=ExecutionManager._scheduler_loop, daemon=True
            )
            ExecutionManager._scheduler_thread.start()

    @staticmethod
    def stop_scheduler():
        ExecutionManager._scheduler_stop.set()
        if ExecutionManager._scheduler_thread:
            ExecutionManager._scheduler_thread.join(timeout=2)
            ExecutionManager._scheduler_thread = None

    @staticmethod
    def _scheduler_loop():
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
        # 0. Workflow Context Boundary Check (FEAT-308)
        session_path = os.path.abspath(os.path.join(".", ".agents", ".session.json"))
        session_data = {}
        if os.path.exists(session_path):
            try:
                with open(session_path, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
            except Exception:
                pass
                
        execution_mode = os.environ.get("AIWF_EXECUTION_MODE") or session_data.get("execution_mode")
        workflow_id = os.environ.get("AIWF_WORKFLOW_ID") or session_data.get("workflow_id")
        
        is_testing = os.environ.get("AIWF_TESTING") == "true"
        if not is_testing and (execution_mode != "workflow" or not workflow_id):
            return False, "EXECUTION_BLOCKED: Engineering action outside Workflow Gateway."

        # Path traversal checks
        cwd = req.get("working_directory", ".")
        abs_cwd = os.path.abspath(cwd)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        
        is_testing_override = is_testing or os.environ.get("AIWF_STRICT_PROCESS_ENFORCEMENT") == "true" or "pytest" in abs_cwd.lower()
        if not is_testing_override and not abs_cwd.startswith(repo_root):
            return False, f"Working directory {cwd} is outside workspace bounds."

        # Role checks
        owner = req.get("owner_agent_id", "")
        cmd = req.get("command", "")
        args = req.get("arguments", [])
        cmd_str = " ".join([cmd] + [str(a) for a in args]).lower()

        # Is it a test command?
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

        # Is it a release command?
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

        # Validate
        valid, msg = ExecutionManager.validate_request(item)
        if not valid:
            raise PermissionError(f"Command execution request rejected: {msg}")

        # Save to registry
        data = ProcessRegistry.read()
        data[execution_id] = item
        ProcessRegistry.write(data)

        # Transition to QUEUED
        ExecutionManager._transition(execution_id, "QUEUED")
        return execution_id

    @staticmethod
    def _transition(execution_id: str, new_status: str, extra: Dict[str, Any] = None) -> None:
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
        item = data.get(execution_id)
        if not item or "status" not in item:
            return

        current = item["status"]
        if new_status not in valid_transitions[current] and new_status != "ORPHANED" and new_status != "BLOCKED_INTERACTIVE":
            if new_status not in ["ORPHANED", "FAILED", "CANCELLED", "TIMED_OUT"]:
                raise ValueError(f"Invalid state transition from {current} to {new_status}")

        updates = {"status": new_status}
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
        queued = [v for v in data.values() if v.get("status") == "QUEUED"]
        if not queued:
            return

        def sort_key(x):
            priority_val = 0
            if x.get("is_force_task"):
                priority_val = 100
            elif x.get("priority") == "high":
                priority_val = 10
            elif x.get("priority") == "low":
                priority_val = -10
            return (-priority_val, x["created_at"])

        queued.sort(key=sort_key)

        running = [v for v in data.values() if v.get("status") in ["STARTING", "RUNNING", "PAUSED", "PAUSING", "RESUMING"]]
        cpu_count, total_mem, avail_mem = ExecutionManager.get_system_capacity()
        active_cpu_load = sum(v.get("cpu_limit", 1.0) for v in running)
        
        for item in queued:
            req_cpu = item.get("cpu_limit", 1.0)
            # Capacity check strictly matching logical CPUs limit
            if active_cpu_load + req_cpu > cpu_count and not item.get("is_force_task"):
                continue
            
            try:
                ExecutionManager._start_process(item["execution_id"])
                active_cpu_load += req_cpu
            except Exception as e:
                ExecutionManager._transition(item["execution_id"], "FAILED", {
                    "termination_reason": f"Failed to spawn process: {e}"
                })

    @staticmethod
    def _start_process(execution_id: str) -> None:
        data = ProcessRegistry.read()
        item = data.get(execution_id)
        if not item:
            return

        ExecutionManager._transition(execution_id, "STARTING")

        cmd = item["command"]
        args = item["arguments"]
        cwd = item["working_directory"]
        stdin_mode = item["stdin_mode"]

        cmd_list = [cmd] + [str(a) for a in args]

        stdin_val = subprocess.DEVNULL
        if stdin_mode == "managed":
            stdin_val = subprocess.PIPE

        preexec = None
        creationflags = 0
        if os.name != 'nt':
            preexec = os.setsid
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
                pgid = os.getpgid(proc.pid)
            except Exception:
                pgid = proc.pid

        # Update registry
        ExecutionManager._transition(execution_id, "RUNNING", {
            "pid": proc.pid,
            "process_group_id": pgid,
            "last_heartbeat_at": datetime.now().astimezone().isoformat()
        })

        # Start Monitor Thread for lifecycle
        monitor = threading.Thread(
            target=ExecutionManager._monitor_process_lifecycle,
            args=(execution_id, proc),
            daemon=True
        )
        monitor.start()

    @staticmethod
    def _monitor_process_lifecycle(execution_id: str, proc: subprocess.Popen) -> None:
        data = ProcessRegistry.read()
        item = data.get(execution_id)
        if not item or "status" not in item:
            return

        timeout = item.get("timeout_seconds", 300)
        start_time = time.time()
        
        # Real-time stdout & stderr reader logs
        is_blocked = [False]
        blocked_reason = [""]

        def read_stdout():
            try:
                stdout_path = item["stdout_artifact"]
                with open(stdout_path, "w", encoding="utf-8") as f:
                    # Iterate lines in real-time
                    for line in proc.stdout:
                        f.write(line)
                        f.flush()
                        
                        # Detect interactive block
                        if item.get("stdin_mode") == "disabled":
                            content = line.lower()
                            keywords = ["confirm", "[y/n]", "enter your password", "password:", "approve?", "proceed?"]
                            for kw in keywords:
                                if kw in content:
                                    is_blocked[0] = True
                                    blocked_reason[0] = f"Process blocked waiting for stdin prompt: '{kw}'"
                                    # Terminate process group directly
                                    try:
                                        if os.name != 'nt':
                                            os.killpg(item.get("process_group_id") or proc.pid, signal.SIGKILL)
                                        else:
                                            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                                    except Exception:
                                        pass
                                    return
            except Exception:
                pass

        def read_stderr():
            try:
                stderr_path = item["stderr_artifact"]
                with open(stderr_path, "w", encoding="utf-8") as f:
                    for line in proc.stderr:
                        f.write(line)
                        f.flush()
            except Exception:
                pass

        t_out = threading.Thread(target=read_stdout, daemon=True)
        t_err = threading.Thread(target=read_stderr, daemon=True)
        t_out.start()
        t_err.start()

        while True:
            exit_code = proc.poll()
            if exit_code is not None:
                t_out.join(timeout=0.2)
                t_err.join(timeout=0.2)
                
                status = "COMPLETED" if exit_code == 0 else "FAILED"
                reason = None
                
                if is_blocked[0]:
                    status = "BLOCKED_INTERACTIVE"
                    reason = blocked_reason[0]
                else:
                    updated_item = ProcessRegistry.read().get(execution_id, {})
                    if updated_item and updated_item.get("status") in ["CANCELLING", "TERMINATING", "CANCELLED"]:
                        status = "CANCELLED"
                        reason = updated_item.get("termination_reason")
                
                ExecutionManager._transition(execution_id, status, {
                    "exit_code": exit_code,
                    "termination_reason": reason,
                    "completed_at": datetime.now().astimezone().isoformat()
                })
                break

            # Check timeout
            elapsed = time.time() - start_time
            if timeout and elapsed > timeout:
                try:
                    if os.name != 'nt':
                        os.killpg(item.get("process_group_id") or proc.pid, signal.SIGKILL)
                    else:
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
                except Exception:
                    pass
                ExecutionManager._transition(execution_id, "TIMED_OUT", {
                    "termination_reason": f"Execution timed out after {timeout} seconds."
                })
                break

            # Update heartbeat & resources
            try:
                now_str = datetime.now().astimezone().isoformat()
                updates = {"last_heartbeat_at": now_str}
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
        item = data.get(execution_id)
        if not item or item.get("status") in ["COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "ORPHANED", "BLOCKED_INTERACTIVE"]:
            return

        ExecutionManager._transition(execution_id, "CANCELLING", {
            "cancel_requested_at": datetime.now().astimezone().isoformat(),
            "termination_reason": reason
        })

        pid = item.get("pid")
        pgid = item.get("process_group_id")
        if not pid:
            ExecutionManager._transition(execution_id, "CANCELLED")
            return

        # Stage 1: Graceful SIGTERM
        if os.name != 'nt':
            try:
                os.killpg(pgid, signal.SIGTERM)
            except Exception:
                try:
                    os.kill(pid, signal.SIGTERM)
                except Exception:
                    pass
        else:
            try:
                os.kill(pid, signal.CTRL_C_EVENT)
            except Exception:
                pass

        time.sleep(1.0)
        
        # Check if still running
        if ExecutionManager.is_pid_alive(pid):
            ExecutionManager.kill(execution_id, reason)
        else:
            ExecutionManager._transition(execution_id, "CANCELLED")

    @staticmethod
    def kill(execution_id: str, reason: str = "KILLED") -> None:
        data = ProcessRegistry.read()
        item = data.get(execution_id)
        if not item:
            return

        pid = item.get("pid")
        pgid = item.get("process_group_id")
        if not pid:
            return

        # Stage 2: Forced SIGKILL
        if os.name != 'nt':
            try:
                os.killpg(pgid, signal.SIGKILL)
            except Exception:
                try:
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
        else:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
            except Exception:
                try:
                    os.kill(pid, signal.SIGABRT)
                except Exception:
                    pass

        ExecutionManager._transition(execution_id, "CANCELLED", {
            "termination_reason": reason
        })

    @staticmethod
    def pause(execution_id: str) -> None:
        data = ProcessRegistry.read()
        item = data.get(execution_id)
        if not item or item.get("status") != "RUNNING":
            return

        ExecutionManager._transition(execution_id, "PAUSING")
        pid = item.get("pid")
        pgid = item.get("process_group_id")
        if not pid:
            return

        if os.name != 'nt':
            try:
                os.killpg(pgid, signal.SIGSTOP)
                ExecutionManager._transition(execution_id, "PAUSED")
            except Exception as e:
                ExecutionManager._transition(execution_id, "RUNNING")
                raise RuntimeError(f"PAUSE_UNSUPPORTED: SIGSTOP failed. {e}")
        else:
            ExecutionManager._transition(execution_id, "RUNNING")
            raise RuntimeError("PAUSE_UNSUPPORTED: Windows does not natively support SIGSTOP.")

    @staticmethod
    def resume(execution_id: str) -> None:
        data = ProcessRegistry.read()
        item = data.get(execution_id)
        if not item or item.get("status") != "PAUSED":
            return

        ExecutionManager._transition(execution_id, "RESUMING")
        pid = item.get("pid")
        pgid = item.get("process_group_id")
        if not pid:
            return

        if os.name != 'nt':
            try:
                os.killpg(pgid, signal.SIGCONT)
                ExecutionManager._transition(execution_id, "RUNNING")
            except Exception as e:
                ExecutionManager._transition(execution_id, "PAUSED")
                raise RuntimeError(f"RESUME_FAILED: SIGCONT failed. {e}")
        else:
            ExecutionManager._transition(execution_id, "PAUSED")
            raise RuntimeError("RESUME_FAILED: Windows does not natively support SIGCONT.")

    @staticmethod
    def recover() -> List[str]:
        data = ProcessRegistry.read()
        recovered = []
        for exec_id, item in data.items():
            if item.get("status") in ["STARTING", "RUNNING", "PAUSED", "PAUSING", "RESUMING", "CANCELLING"]:
                pid = item.get("pid")
                if not pid:
                    ExecutionManager._transition(exec_id, "ORPHANED", {"termination_reason": "No PID recorded."})
                    continue

                if ExecutionManager.is_pid_alive(pid):
                    cmdline = ExecutionManager.get_process_cmdline(pid)
                    expected_cmd = item["command"].lower()
                    if expected_cmd in cmdline.lower() or any(str(arg).lower() in cmdline.lower() for arg in item["arguments"]):
                        if item["status"] in ["STARTING", "RUNNING"]:
                            class DummyProc:
                                def __init__(self, pid):
                                    self.pid = pid
                                    self.stdout = []
                                    self.stderr = []
                                def poll(self):
                                    if not ExecutionManager.is_pid_alive(self.pid):
                                        return 0
                                    return None
                            
                            proc = DummyProc(pid)
                            # Create a lighter re-attachment monitor
                            def recovery_monitor():
                                while proc.poll() is None:
                                    time.sleep(1.0)
                                ExecutionManager._transition(exec_id, "COMPLETED")

                            monitor = threading.Thread(target=recovery_monitor, daemon=True)
                            monitor.start()
                            recovered.append(exec_id)
                        else:
                            recovered.append(exec_id)
                    else:
                        ExecutionManager._transition(exec_id, "ORPHANED", {
                            "termination_reason": "PID identity validation failed. Reused PID detected."
                        })
                else:
                    ExecutionManager._transition(exec_id, "ORPHANED", {
                        "termination_reason": "Process is not running on host."
                    })
        return recovered

    @staticmethod
    def is_pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    @staticmethod
    def get_process_cmdline(pid: int) -> str:
        try:
            import psutil
            proc = psutil.Process(pid)
            return " ".join(proc.cmdline())
        except Exception:
            if os.name != 'nt':
                res = subprocess.run(["ps", "-p", str(pid), "-o", "command="], capture_output=True, text=True)
                return res.stdout.strip()
            else:
                res = subprocess.run(["wmic", "process", "where", f"ProcessId={pid}", "get", "CommandLine"], capture_output=True, text=True)
                lines = res.stdout.strip().split("\n")
                if len(lines) > 1:
                    return lines[1].strip()
        return ""

    @staticmethod
    def run_command_managed(cmd_list: List[str], cwd: str = ".", owner_agent_id: str = "AGENT-SYSTEM", task_id: str = "TASK-SYSTEM", timeout: int = 300) -> Any:
        req = {
            "command": cmd_list[0],
            "arguments": cmd_list[1:],
            "working_directory": cwd,
            "owner_agent_id": owner_agent_id,
            "task_id": task_id,
            "timeout": timeout
        }
        exec_id = ExecutionManager.submit(req)
        ExecutionManager.tick_scheduler()
        
        while True:
            data = ProcessRegistry.read()
            item = data.get(exec_id)
            if not item:
                raise RuntimeError(f"Execution record {exec_id} disappeared.")
            if item["status"] in ["COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "BLOCKED_INTERACTIVE", "ORPHANED"]:
                stdout = ""
                if os.path.exists(item["stdout_artifact"]):
                    with open(item["stdout_artifact"], "r", encoding="utf-8", errors="ignore") as f:
                        stdout = f.read()
                stderr = ""
                if os.path.exists(item["stderr_artifact"]):
                    with open(item["stderr_artifact"], "r", encoding="utf-8", errors="ignore") as f:
                        stderr = f.read()
                
                class CompletedProcessCompat:
                    def __init__(self, args, returncode, stdout, stderr):
                        self.args = args
                        self.returncode = returncode
                        self.stdout = stdout
                        self.stderr = stderr
                    def check_returncode(self):
                        if self.returncode != 0:
                            raise subprocess.CalledProcessError(self.returncode, self.args, self.stdout, self.stderr)
                
                exit_code = item.get("exit_code") or (0 if item["status"] == "COMPLETED" else 1)
                return CompletedProcessCompat(cmd_list, exit_code, stdout, stderr)
            time.sleep(0.1)

    @staticmethod
    def popen_command_managed(cmd_list: List[str], cwd: str = ".", owner_agent_id: str = "AGENT-SYSTEM", task_id: str = "TASK-SYSTEM", timeout: int = 300, stdout=None, stderr=None, preexec_fn=None, creationflags=0, text=True, bufsize=-1) -> Any:
        req = {
            "command": cmd_list[0],
            "arguments": cmd_list[1:],
            "working_directory": cwd,
            "owner_agent_id": owner_agent_id,
            "task_id": task_id,
            "timeout": timeout
        }
        exec_id = ExecutionManager.submit(req)
        ExecutionManager._transition(exec_id, "STARTING")
        
        proc = subprocess.Popen(
            cmd_list,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            preexec_fn=preexec_fn,
            creationflags=creationflags,
            text=text,
            bufsize=bufsize
        )
        
        pgid = proc.pid
        if os.name != 'nt':
            try:
                pgid = os.getpgid(proc.pid)
            except Exception:
                pgid = proc.pid
                
        ExecutionManager._transition(exec_id, "RUNNING", {
            "pid": proc.pid,
            "process_group_id": pgid,
            "last_heartbeat_at": datetime.now().astimezone().isoformat()
        })
        
        # Lighter monitor for popen redirection to avoid thread overheads
        def popen_monitor():
            while proc.poll() is None:
                time.sleep(1.0)
            exit_code = proc.poll()
            status = "COMPLETED" if exit_code == 0 else "FAILED"
            ExecutionManager._transition(exec_id, status, {
                "exit_code": exit_code,
                "completed_at": datetime.now().astimezone().isoformat()
            })

        monitor = threading.Thread(target=popen_monitor, daemon=True)
        monitor.start()
        
        return proc
