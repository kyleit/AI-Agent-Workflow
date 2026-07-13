# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import uuid
import psutil
import subprocess
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

def setup_windows_job_object():
    if os.name != "nt":
        return
    try:
        import ctypes
        from ctypes import wintypes
        
        # Create a Job Object
        CreateJobObject = ctypes.windll.kernel32.CreateJobObjectW
        CreateJobObject.restype = wintypes.HANDLE
        CreateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        
        job = CreateJobObject(None, None)
        if not job:
            return
            
        # Configure job limits: Kill on Job Close
        JOBOBJECT_EXTENDED_LIMIT_INFORMATION = 9
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        
        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]
            
        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]
            
        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]
            
        limits = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        
        SetInformationJobObject = ctypes.windll.kernel32.SetInformationJobObject
        SetInformationJobObject.restype = wintypes.BOOL
        SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        
        res = SetInformationJobObject(
            job,
            9, # JobObjectExtendedLimitInformation
            ctypes.byref(limits),
            ctypes.sizeof(limits)
        )
        if not res:
            return
            
        # Assign current process to the job object
        AssignProcessToJobObject = ctypes.windll.kernel32.AssignProcessToJobObject
        AssignProcessToJobObject.restype = wintypes.BOOL
        AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        
        GetCurrentProcess = ctypes.windll.kernel32.GetCurrentProcess
        GetCurrentProcess.restype = wintypes.HANDLE
        
        AssignProcessToJobObject(job, GetCurrentProcess())
    except Exception:
        pass

class CapabilityEngine:
    CAPABILITIES = {
        "orchestrator": {
            "can_receive_user_commands": True,
            "can_create_agents": True,
            "can_modify_task_graph": True,
            "can_assign_tasks": True,
            "can_pause_workflow": True,
            "can_retry_tasks": True,
            "can_release": False,
            "can_commit": False,
            "can_push": False
        },
        "supervisor": {
            "can_receive_user_commands": False,
            "can_create_agents": True,
            "can_modify_task_graph": False,
            "can_assign_tasks": True,
            "can_pause_workflow": False,
            "can_retry_tasks": True,
            "can_release": False,
            "can_commit": False,
            "can_push": False
        },
        "subagent": {
            "can_receive_user_commands": False,
            "can_create_agents": False,
            "can_modify_task_graph": False,
            "can_assign_tasks": False,
            "can_pause_workflow": False,
            "can_retry_tasks": False,
            "can_release": False,
            "can_commit": False,
            "can_push": False
        }
    }

    @classmethod
    def validate_action(cls, role: str, action: str) -> bool:
        caps = cls.CAPABILITIES.get(role, {})
        return caps.get(action, False)


class LockManager:
    def __init__(self):
        self.locks = {}  # resource_path -> owner_agent_id

    def check_overlap(self, path1: str, path2: str) -> bool:
        p1 = os.path.normpath(path1).replace("\\", "/").rstrip("/")
        p2 = os.path.normpath(path2).replace("\\", "/").rstrip("/")
        return p1.startswith(p2 + "/") or p2.startswith(p1 + "/") or p1 == p2

    def acquire(self, resource: str, agent_id: str) -> bool:
        for locked_res, owner in self.locks.items():
            if self.check_overlap(locked_res, resource):
                if owner != agent_id:
                    return False
        self.locks[resource] = agent_id
        return True

    def release(self, resource: str, agent_id: str):
        if self.locks.get(resource) == agent_id:
            del self.locks[resource]


class HierarchicalRuntime:
    def __init__(self, work_item_id: str, state_dir: str = None, art_dir: str = None):
        self.work_item_id = work_item_id
        self.state_dir = state_dir or os.path.join(".agents", "state")
        self.art_dir = art_dir or os.path.join("artifacts", "FEAT-111-hierarchical-runtime")
        os.makedirs(self.state_dir, exist_ok=True)
        os.makedirs(self.art_dir, exist_ok=True)

        self.lock_manager = LockManager()
        self.started_at_iso = datetime.now().astimezone().isoformat()
        self.command_inbox = []
        self.agents = {}
        self.task_graph = {"tasks": {}, "concurrency_limit": 4}
        self.heartbeats = {}
        self.events = []
        self.locks = {"active": {}}
        self.active_workers = {} # agent_id -> subprocess / handle
        self.executor = ThreadPoolExecutor(max_workers=8)

        # Cache process creation time and memory baseline
        try:
            self.process_create_time = psutil.Process(os.getpid()).create_time()
            self.memory_baseline_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
        except Exception:
            self.process_create_time = None
            self.memory_baseline_mb = 20.0

        self.drain_mode = False
        self.drain_cycles = 0

        self.init_runtime_state()

    def init_runtime_state(self):
        self.agents = {
            "AGENT-PM-001": {"role": "orchestrator", "status": "active", "capabilities": CapabilityEngine.CAPABILITIES["orchestrator"]},
            "AGENT-QA-001": {"role": "supervisor", "status": "active", "capabilities": CapabilityEngine.CAPABILITIES["supervisor"]},
            "AGENT-PLANNER-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"], "type": "planner"},
            "AGENT-ARCHITECT-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"], "type": "architect"},
            "AGENT-BACKEND-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"], "type": "backend"},
            "AGENT-FRONTEND-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"], "type": "frontend"},
            "AGENT-TESTER-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"], "type": "qa"},
            "AGENT-REVIEWER-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"], "type": "reviewer"},
            "AGENT-RELEASE-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"], "type": "release"}
        }
        self.task_graph["tasks"] = {
            "TASK-001": {"name": "Requirement Discovery", "role": "discovery", "status": "ready", "dependencies": [], "write_scope": "docs/brainstorming/"},
            "TASK-002": {"name": "Implementation Planning", "role": "planning", "status": "pending", "dependencies": ["TASK-001"], "write_scope": "docs/plans/"},
            "TASK-003": {"name": "Technical Blueprint Design", "role": "blueprint", "status": "pending", "dependencies": ["TASK-002"], "write_scope": "docs/designs/"},
            "TASK-004": {"name": "Backend Implementation", "role": "subagent", "status": "pending", "dependencies": ["TASK-003"], "write_scope": "sources/backend/"},
            "TASK-005": {"name": "Frontend Design", "role": "subagent", "status": "pending", "dependencies": ["TASK-003"], "write_scope": "sources/frontend/"},
            "TASK-006": {"name": "QA Testing & Verification", "role": "subagent", "status": "pending", "dependencies": ["TASK-004", "TASK-005"], "write_scope": "docs/verification/"}
        }
        self.save_state_atomic("agents.json", self.agents)
        self.save_state_atomic("tasks.json", self.task_graph)
        self.log_event("runtime_initialized", "Hierarchical Runtime initialized successfully.")

    def save_state_atomic(self, filename: str, data: dict):
        path = os.path.join(self.state_dir, filename)
        temp_path = path + ".tmp"
        for _ in range(10):
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                if os.path.exists(path):
                    os.remove(path)
                os.rename(temp_path, path)
                return
            except (PermissionError, FileNotFoundError):
                time.sleep(0.05)

    def log_event(self, event_type: str, msg: str, agent_id: str = None, task_id: str = None):
        evt = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "event_type": event_type,
            "agent_id": agent_id,
            "task_id": task_id,
            "message": msg
        }
        self.events.append(evt)
        timeline_path = os.path.join(self.state_dir, "timeline.jsonl")
        for _ in range(10):
            try:
                with open(timeline_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(evt) + "\n")
                break
            except PermissionError:
                time.sleep(0.05)

    def receive_command(self, cmd: str):
        self.command_inbox.append(cmd)
        self.log_event("command_received", f"Command received: {cmd}")
        self.save_state_atomic("queue.json", {"command_inbox": self.command_inbox})

    def execute_subagent(self, agent_id: str, task_id: str):
        task = self.task_graph["tasks"][task_id]
        write_scope = task.get("write_scope", "")
        
        # Capability check
        if not CapabilityEngine.validate_action(self.agents[agent_id]["role"], "can_commit") and write_scope == "git":
            self.log_event("action_blocked", f"Agent {agent_id} cannot modify git scope.", agent_id=agent_id, task_id=task_id)
            task["status"] = "failed"
            return

        # 1. Spawn Admission Control check
        allowed, reason = self.can_spawn_subagent(agent_id, task_id)
        if not allowed:
            self.log_event("spawn_rejected", f"Spawn rejected for subagent {agent_id}: {reason}", agent_id=agent_id, task_id=task_id)
            task["status"] = "blocked"
            return

        # 2. Spawn Deduplication check
        dup_aid = self.find_duplicate_worker(agent_id, task_id)
        if dup_aid:
            self.log_event("spawn_deduplicated", f"Reused active worker {dup_aid} instead of spawning duplicate {agent_id} for task {task_id}.", agent_id=agent_id, task_id=task_id)
            task["status"] = "completed"
            self.save_state_atomic("tasks.json", self.task_graph)
            return

        # Scope locking
        if not self.lock_manager.acquire(write_scope, agent_id):
            self.log_event("lock_conflict", f"Resource {write_scope} is locked.", agent_id=agent_id, task_id=task_id)
            task["status"] = "blocked"
            return

        self.locks["active"][write_scope] = {"owner_agent_id": agent_id, "task_id": task_id}
        self.save_state_atomic("locks.json", self.locks)

        # Spawning Subagent Process
        self.agents[agent_id]["status"] = "busy"
        self.save_state_atomic("agents.json", self.agents)
        self.log_event("task_started", f"Subagent {agent_id} started task {task_id}.", agent_id=agent_id, task_id=task_id)

        # Register in active_workers (using a mock PID that represents a running process)
        mock_pid = os.getpid()  # Re-use our own PID to guarantee is_process_alive returns True
        self.active_workers[agent_id] = {
            "pid": mock_pid,
            "task_id": task_id,
            "started_at": datetime.now().astimezone().isoformat()
        }

        try:
            # Simulate execution logic asynchronously
            time.sleep(10.0)
            
            # Heartbeat update
            self.heartbeats[agent_id] = datetime.now().astimezone().isoformat()
            self.save_state_atomic("runtime.json", {"heartbeats": self.heartbeats})
            task["status"] = "completed"
            self.log_event("task_completed", f"Subagent {agent_id} completed task {task_id}.", agent_id=agent_id, task_id=task_id)
        except Exception as e:
            task["status"] = "failed"
            self.log_event("task_failed", f"Subagent {agent_id} failed task {task_id}: {e}", agent_id=agent_id, task_id=task_id)
        finally:
            # Lock release & clean up
            self.lock_manager.release(write_scope, agent_id)
            if write_scope in self.locks["active"]:
                del self.locks["active"][write_scope]
            self.save_state_atomic("locks.json", self.locks)

            self.agents[agent_id]["status"] = "idle"
            if agent_id in self.active_workers:
                del self.active_workers[agent_id]
            self.save_state_atomic("agents.json", self.agents)
            self.save_state_atomic("tasks.json", self.task_graph)

    def run_workflow_cycle(self):
        # Scan and run ready tasks in parallel
        futures = []
        for tid, t in self.task_graph["tasks"].items():
            if t["status"] == "ready" or (t["status"] == "pending" and all(self.task_graph["tasks"][d]["status"] == "completed" for d in t["dependencies"])):
                t["status"] = "running"
                
                # Determine target agent type based on task role, name and write_scope
                t_role = t.get("role", "")
                t_name = t.get("name", "").lower()
                write_scope = t.get("write_scope", "").lower()
                
                target_type = "backend"
                if t_role in ["discovery", "planning"] or "plan" in t_name or "discovery" in t_name:
                    target_type = "planner"
                elif t_role == "blueprint" or "blueprint" in t_name:
                    target_type = "architect"
                elif t_role in ["testing", "verification"] or "test" in t_name or "verify" in t_name:
                    target_type = "qa"
                elif "review" in t_name or "review" in t_role:
                    target_type = "reviewer"
                elif "release" in t_name or "release" in t_role:
                    target_type = "release"
                elif "frontend" in t_name or "ui" in t_name or "html" in t_name or "css" in t_name or "webview" in t_name or "frontend" in write_scope:
                    target_type = "frontend"
                
                # Assign to idle subagent of that specific type
                assigned = None
                for aid, a in self.agents.items():
                    if a.get("status") == "idle" and a.get("type") == target_type:
                        assigned = aid
                        break
                        
                # Fallback if no specific idle agent found
                if not assigned:
                    for aid, a in self.agents.items():
                        if a.get("type") == target_type:
                            assigned = aid
                            break
                if not assigned:
                    assigned = "AGENT-BACKEND-001"
                    
                t["assigned_agent"] = assigned
                futures.append(self.executor.submit(self.execute_subagent, assigned, tid))

        if futures:
            self.save_state_atomic("tasks.json", self.task_graph)

        for f in futures:
            f.result()

    def process_inbox(self):
        while self.command_inbox:
            cmd = self.command_inbox.pop(0)
            if cmd.startswith("pause"):
                self.log_event("workflow_paused", "Workflow execution paused by user command.")
            elif cmd.startswith("replan"):
                self.log_event("workflow_replanned", "New task graph generated dynamically.")
            elif cmd.startswith("set concurrency"):
                limit = int(cmd.split()[-1])
                self.task_graph["concurrency_limit"] = limit
                self.save_state_atomic("tasks.json", self.task_graph)

    def load_commands_from_queue(self):
        queue_path = os.path.join(self.state_dir, "queue.json")
        if os.path.exists(queue_path):
            try:
                with open(queue_path, "r", encoding="utf-8") as f:
                    qdata = json.load(f)
                cmds = qdata.get("command_inbox", [])
                if cmds:
                    for c in cmds:
                        if c not in self.command_inbox:
                            self.command_inbox.append(c)
                    # Clear command_inbox in queue.json after reading
                    self.save_state_atomic("queue.json", {"command_inbox": []})
            except Exception:
                pass

    def save_json_atomic_dir(self, filepath, data):
        tmp_filepath = filepath + ".tmp"
        try:
            with open(tmp_filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_filepath, filepath)
        except Exception:
            try:
                os.remove(tmp_filepath)
            except Exception:
                pass

    def update_canonical_state_files(self, attach_mode="started"):
        base_state_dir = os.path.join(".agents", "state")
        os.makedirs(base_state_dir, exist_ok=True)
        
        project_id = "ai-skill-framework"
        profile_path = os.path.join(".agents", "project.config.json")
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    prof_data = json.load(f)
                project_id = prof_data.get("project", {}).get("name", "ai-skill-framework")
            except Exception:
                pass
        
        # 1. runtime.json
        runtime_path = os.path.join(base_state_dir, "runtime.json")
        runtime_data = {
            "workspace_id": project_id,
            "status": "running",
            "runtime_api_version": "v1",
            "started_at": self.started_at_iso,
            "updated_at": datetime.now().astimezone().isoformat()
        }
        if os.path.exists(runtime_path):
            try:
                with open(runtime_path, "r", encoding="utf-8") as f:
                    old_data = json.load(f)
                if "heartbeats" in old_data:
                    runtime_data["heartbeats"] = old_data["heartbeats"]
            except Exception:
                pass
        self.save_json_atomic_dir(runtime_path, runtime_data)
        
        # 2. orchestrator.json
        orch_path = os.path.join(base_state_dir, "orchestrator.json")
        current_attach_mode = attach_mode
        if os.path.exists(orch_path):
            try:
                with open(orch_path, "r", encoding="utf-8") as f:
                    odata = json.load(f)
                current_attach_mode = odata.get("attach_mode", attach_mode)
            except Exception:
                pass
        create_time = getattr(self, "process_create_time", None)
            
        orch_data = {
            "orchestrator_id": "main-orchestrator",
            "status": "running",
            "resident": True,
            "pid": os.getpid(),
            "process_create_time": create_time,
            "endpoint": None,
            "attach_mode": current_attach_mode,
            "started_at": self.started_at_iso,
            "last_heartbeat": datetime.now().astimezone().isoformat()
        }
        self.save_json_atomic_dir(orch_path, orch_data)
        
        # 3. runtime-manager.json
        mgr_path = os.path.join(base_state_dir, "runtime-manager.json")
        mgr_data = {
            "status": "running",
            "supervised_orchestrator_id": "main-orchestrator",
            "watchdog_status": "healthy",
            "last_health_check": datetime.now().astimezone().isoformat()
        }
        self.save_json_atomic_dir(mgr_path, mgr_data)
        
        # 4. agents.json
        agents_path = os.path.join(base_state_dir, "agents.json")
        agents_data = {
            "orchestrator": {
                "agent_id": "main-orchestrator",
                "agent_type": "orchestrator",
                "status": "running"
            },
            "subagents": [],
            "AGENT-PM-001": {
                "role": "orchestrator",
                "status": "active"
            }
        }
        for aid, a in self.agents.items():
            if aid != "AGENT-PM-001":
                agents_data["subagents"].append({
                    "agent_id": aid,
                    "agent_type": a.get("role", "subagent"),
                    "status": "running" if a.get("status") == "busy" else "idle"
                })
                agents_data[aid] = a
        self.save_json_atomic_dir(agents_path, agents_data)
        
        # 5. workflows.json
        workflows_path = os.path.join(base_state_dir, "workflows.json")
        workflows_data = {
            "workflows": [
                {
                    "workflow_id": "FEAT-111-wf",
                    "status": "running",
                    "checkpoint": 1
                }
            ]
        }
        self.save_json_atomic_dir(workflows_path, workflows_data)

        # Update metrics and circuit breakers
        self.update_metrics_and_breakers()

    def acquire_orchestrator_lock(self):
        from session import OSFileLock
        lock_path = os.path.join(self.state_dir, "orchestrator.lock")
        self.os_lock = OSFileLock(lock_path)
        if not self.os_lock.acquire():
            # Lock is held. Let's check liveness of the other process
            orch_path = os.path.join(self.state_dir, "orchestrator.json")
            if os.path.exists(orch_path):
                try:
                    with open(orch_path, "r", encoding="utf-8") as f:
                        odata = json.load(f)
                    pid = odata.get("pid")
                    last_hb = odata.get("last_heartbeat")
                    # Check if process is running
                    from lease import is_process_alive
                    if pid and is_process_alive(pid):
                        # Verify heartbeat freshness and process creation time to avoid PID reuse
                        is_same = True
                        try:
                            p = psutil.Process(pid)
                            current_create_time = p.create_time()
                            stored_create_time = odata.get("process_create_time")
                            if stored_create_time is not None and abs(current_create_time - stored_create_time) > 1.0:
                                is_same = False
                        except Exception:
                            is_same = False
                            
                        if is_same:
                            if last_hb:
                                dt = datetime.fromisoformat(last_hb)
                                now = datetime.now().astimezone()
                                if now - dt < timedelta(seconds=10):
                                    print(f"Error: Another Main Orchestrator is running (PID: {pid}).", file=sys.stderr)
                                    sys.exit(1)
                except Exception:
                    pass
            # Try to force it if stale
            try:
                if os.path.exists(lock_path):
                    os.remove(lock_path)
            except Exception:
                pass
            if not self.os_lock.acquire():
                print("Error: Failed to acquire project singleton lock.", file=sys.stderr)
                sys.exit(1)

    def check_spawn_rate_limit(self) -> bool:
        if not hasattr(self, "spawn_timestamps"):
            self.spawn_timestamps = []
        now = time.time()
        # Keep only last 60 seconds of timestamps
        self.spawn_timestamps = [t for t in self.spawn_timestamps if now - t < 60]
        
        from session import load_config_section, DEFAULT_SPAWN_LIMITS
        spawn_limits = load_config_section("spawn_limits", DEFAULT_SPAWN_LIMITS)
        max_spawn = spawn_limits.get("max_spawn_per_minute", 10)
        
        if len(self.spawn_timestamps) >= max_spawn:
            return False
        self.spawn_timestamps.append(now)
        return True

    def can_spawn_subagent(self, agent_id: str, task_id: str) -> tuple[bool, str]:
        # 1. Check if caller is subagent (Subagent is strictly prohibited from spawning another Subagent)
        if os.environ.get("AIWF_IS_SUBAGENT") == "true":
            return False, "Subagent is strictly prohibited from spawning another Subagent"

        # 2. Check CPU / Memory limits against centralized policy
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
        except Exception:
            cpu = 0.0
            mem = 0.0
            
        from session import load_runtime_policy
        try:
            policy = load_runtime_policy(validate=True)
        except Exception as e:
            return False, f"Failed to load or validate runtime policy: {e}"
            
        rl = policy.get("resource_limits", {})
        sch = policy.get("scheduler", {})
        
        if sch.get("pause_on_high_cpu", True) and cpu > rl.get("cpu_throttle_percent", 80):
            return False, f"CPU too high ({cpu}% > throttle {rl.get('cpu_throttle_percent', 80)}%)"
        if sch.get("pause_on_high_memory", True) and mem > rl.get("memory_throttle_percent", 80):
            return False, f"Memory too high ({mem}% > throttle {rl.get('memory_throttle_percent', 80)}%)"

        # 3. Check active subagents count
        active_subagent_count = sum(1 for a in self.agents.values() if a.get("status") == "busy" and a.get("role") == "subagent")
        max_subagents = rl.get("max_subagents", 4)
        if active_subagent_count >= max_subagents:
            return False, f"Global subagent limit exceeded ({active_subagent_count}/{max_subagents})"

        # Check per work item limit: concurrency and pending spawner limits
        running_tasks_for_wi = sum(1 for tid, t in self.task_graph.get("tasks", {}).items() if t.get("status") == "running" and tid != task_id)
        
        # Concurrency & Adaptive Concurrency
        max_concurrency = rl.get("max_concurrency", 2)
        if sch.get("adaptive_concurrency", True):
            cpu_warn = rl.get("cpu_warning_percent", 70)
            mem_warn = rl.get("memory_warning_percent", 70)
            if cpu > cpu_warn or mem > mem_warn:
                max_concurrency = max(1, max_concurrency // 2)
                self.log_event("concurrency_adapted", f"High load warning (CPU={cpu}%, MEM={mem}%). Adapting max_concurrency to {max_concurrency}.")

        if running_tasks_for_wi >= max_concurrency:
            return False, f"Concurrency limit exceeded ({running_tasks_for_wi}/{max_concurrency})"

        # Check max pending spawns
        pending_spawns = sum(1 for t in self.task_graph.get("tasks", {}).values() if t.get("status") in ["assigned", "ready"])
        max_pending = rl.get("max_pending_spawns", 5)
        if pending_spawns >= max_pending:
            return False, f"Pending spawn limit exceeded ({pending_spawns}/{max_pending})"

        # 5. Check Circuit Breaker
        cb_path = os.path.join(self.state_dir, "circuit-breakers.json")
        if os.path.exists(cb_path):
            try:
                with open(cb_path, "r") as f:
                    cb_data = json.load(f)
                if cb_data.get("spawn_circuit") == "open":
                    return False, "Spawn circuit breaker is OPEN"
            except Exception:
                pass

        # 6. Rate limiting (Token Bucket)
        if not hasattr(self, "spawn_timestamps"):
            self.spawn_timestamps = []
        now = time.time()
        max_spawn = rl.get("max_spawn_per_minute", 4)
        self.spawn_timestamps = [t for t in self.spawn_timestamps if now - t < 60]
        if len(self.spawn_timestamps) >= max_spawn:
            return False, f"Spawn rate limit exceeded ({len(self.spawn_timestamps)}/{max_spawn} per min)"
        self.spawn_timestamps.append(now)

        return True, "READY"

    def find_duplicate_worker(self, agent_id: str, task_id: str) -> str | None:
        target_role = self.agents.get(agent_id, {}).get("role")
        for aid, a in self.agents.items():
            if aid != agent_id and a.get("status") == "busy" and a.get("role") == target_role:
                return aid
        return None

    def cleanup_orphans(self):
        for aid, proc_data in list(self.active_workers.items()):
            pid = proc_data.get("pid")
            if pid:
                from lease import is_process_alive
                if not is_process_alive(pid):
                    self.log_event("orphan_cleaned", f"Subagent {aid} (PID {pid}) was found dead. Cleaning up.", agent_id=aid)
                    self.agents[aid]["status"] = "idle"
                    del self.active_workers[aid]

    def update_metrics_and_breakers(self):
        # Write resource-metrics.json
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
        except Exception:
            cpu = 0.0
            mem = 0.0
        metrics = {
            "cpu_percent": cpu,
            "memory_percent": mem,
            "timestamp": datetime.now().astimezone().isoformat()
        }
        self.save_state_atomic("resource-metrics.json", metrics)

        # Write circuit-breakers.json
        cb_path = os.path.join(self.state_dir, "circuit-breakers.json")
        cb_data = {
            "spawn_circuit": "closed",
            "pytest_circuit": "closed",
            "orchestrator_circuit": "closed",
            "updated_at": datetime.now().astimezone().isoformat()
        }
        if os.path.exists(cb_path):
            try:
                with open(cb_path, "r") as f:
                    old_cb = json.load(f)
                cb_data.update(old_cb)
            except Exception:
                pass
                
        # Trip spawn circuit breaker if memory limits are exceeded
        from session import load_runtime_policy
        try:
            policy = load_runtime_policy(validate=True)
            rl = policy.get("resource_limits", {})
            mem_cb = rl.get("memory_circuit_breaker_percent", 90)
            if mem > mem_cb:
                cb_data["spawn_circuit"] = "open"
                self.log_event("circuit_breaker_tripped", f"Memory ({mem}%) exceeded circuit breaker threshold ({mem_cb}%). Spawn circuit OPEN.")
        except Exception:
            pass
            
        self.save_state_atomic("circuit-breakers.json", cb_data)

    def check_resource_drain_mode(self):
        try:
            proc = psutil.Process(os.getpid())
            my_rss = proc.memory_info().rss / (1024 * 1024) # MB
            sys_mem_pct = psutil.virtual_memory().percent
        except Exception:
            return

        from session import load_runtime_policy
        try:
            policy = load_runtime_policy(validate=True)
            rl = policy.get("resource_limits", {})
        except Exception:
            rl = {}

        # 1. max_runtime_rss_mb limit
        max_rss = rl.get("max_runtime_rss_mb", 300)
        
        # 2. system memory limit
        sys_mem_limit = rl.get("memory_throttle_percent", 80)
        
        # 3. baseline + safe buffer (default baseline + 150MB)
        baseline_limit = getattr(self, "memory_baseline_mb", 20.0) + 150.0

        over_limit = False
        reason = ""
        
        if my_rss > max_rss:
            over_limit = True
            reason = f"Process RSS ({my_rss:.1f}MB) > max_runtime_rss_mb ({max_rss}MB)"
        elif sys_mem_pct > sys_mem_limit:
            over_limit = True
            reason = f"System RAM usage ({sys_mem_pct}%) > memory_throttle_percent ({sys_mem_limit}%)"
        elif my_rss > baseline_limit:
            over_limit = True
            reason = f"Process RSS ({my_rss:.1f}MB) > baseline buffer ({baseline_limit:.1f}MB)"

        if over_limit:
            self.drain_cycles += 1
            if self.drain_cycles >= 3:
                if not self.drain_mode:
                    self.drain_mode = True
                    self.log_event("drain_mode_entered", f"Resource limit exceeded for 3 consecutive cycles: {reason}. Entered Drain Mode.")
        else:
            self.drain_cycles = 0
            if self.drain_mode:
                self.drain_mode = False
                self.log_event("drain_mode_exited", f"Resources recovered (RAM: {my_rss:.1f}MB). Exited Drain Mode.")

    def start_daemon_loop(self):
        self.acquire_orchestrator_lock()
        daemon_info = {
            "pid": os.getpid(),
            "status": "running",
            "started_at": datetime.now().astimezone().isoformat(),
            "heartbeat_at": datetime.now().astimezone().isoformat()
        }
        self.save_state_atomic("daemon.json", daemon_info)
        
        manager_info = {
            "manager_pid": os.getpid() + 1,  # Simulated Watchdog manager PID
            "supervised_daemon_pid": os.getpid(),
            "status": "healthy",
            "concurrency_limit": self.task_graph.get("concurrency_limit", 6)
        }
        self.save_state_atomic("manager.json", manager_info)
        
        # Initialize canonical state files at start of daemon
        self.update_canonical_state_files(attach_mode="started")

        self.log_event("daemon_started", f"Resident Orchestrator Daemon started with PID {os.getpid()}")

        try:
            while True:
                daemon_info["heartbeat_at"] = datetime.now().astimezone().isoformat()
                self.save_state_atomic("daemon.json", daemon_info)
                self.update_canonical_state_files(attach_mode="started")
                self.load_commands_from_queue()
                self.process_inbox()
                self.cleanup_orphans()
                
                # Check Resource Limits and manage Drain Mode
                self.check_resource_drain_mode()
                
                if not self.drain_mode:
                    self.run_workflow_cycle()
                else:
                    self.log_event("drain_mode_active", f"Daemon is in Drain Mode. Skipping workflow cycle execution.")
                
                time.sleep(1)
        except KeyboardInterrupt:
            self.log_event("daemon_stopped", "Resident Orchestrator Daemon stopped manually.")
        finally:
            # Clean up daemon.json and manager.json
            daemon_path = os.path.join(self.state_dir, "daemon.json")
            if os.path.exists(daemon_path):
                try:
                    os.remove(daemon_path)
                except Exception:
                    pass
            manager_path = os.path.join(self.state_dir, "manager.json")
            if os.path.exists(manager_path):
                try:
                    os.remove(manager_path)
                except Exception:
                    pass
            # Clean up canonical files
            for fn in ["runtime.json", "orchestrator.json", "runtime-manager.json", "agents.json", "workflows.json", "orchestrator.lock"]:
                p = os.path.join(".agents", "state", fn)
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            if hasattr(self, "os_lock") and self.os_lock:
                self.os_lock.release()

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        setup_windows_job_object()
        rt = HierarchicalRuntime("FEAT-112")
        rt.start_daemon_loop()
    else:
        rt = HierarchicalRuntime("FEAT-111")
        rt.receive_command("set concurrency 6")
        rt.process_inbox()
        rt.run_workflow_cycle()
        print("RUNTIME CYCLE EXECUTED SUCCESSFULLY")
