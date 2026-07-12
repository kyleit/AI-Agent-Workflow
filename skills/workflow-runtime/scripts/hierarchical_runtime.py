# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import uuid
import psutil
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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
        self.command_inbox = []
        self.agents = {}
        self.task_graph = {"tasks": {}, "concurrency_limit": 4}
        self.heartbeats = {}
        self.events = []
        self.locks = {"active": {}}
        self.active_workers = {} # agent_id -> subprocess / handle
        self.executor = ThreadPoolExecutor(max_workers=8)

        self.init_runtime_state()

    def init_runtime_state(self):
        self.agents = {
            "AGENT-PM-001": {"role": "orchestrator", "status": "active", "capabilities": CapabilityEngine.CAPABILITIES["orchestrator"]},
            "AGENT-QA-001": {"role": "supervisor", "status": "active", "capabilities": CapabilityEngine.CAPABILITIES["supervisor"]},
            "AGENT-BACKEND-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"]},
            "AGENT-FRONTEND-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"]},
            "AGENT-TESTER-001": {"role": "subagent", "status": "idle", "capabilities": CapabilityEngine.CAPABILITIES["subagent"]}
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

        # Simulate execution logic asynchronously
        time.sleep(0.2)
        
        # Heartbeat update
        self.heartbeats[agent_id] = datetime.now().astimezone().isoformat()
        self.save_state_atomic("runtime.json", {"heartbeats": self.heartbeats})

        # Lock release & clean up
        self.lock_manager.release(write_scope, agent_id)
        if write_scope in self.locks["active"]:
            del self.locks["active"][write_scope]
        self.save_state_atomic("locks.json", self.locks)

        task["status"] = "completed"
        self.agents[agent_id]["status"] = "idle"
        self.save_state_atomic("agents.json", self.agents)
        self.save_state_atomic("tasks.json", self.task_graph)
        self.log_event("task_completed", f"Subagent {agent_id} completed task {task_id}.", agent_id=agent_id, task_id=task_id)

    def run_workflow_cycle(self):
        # Scan and run ready tasks in parallel
        futures = []
        for tid, t in self.task_graph["tasks"].items():
            if t["status"] == "ready" or (t["status"] == "pending" and all(self.task_graph["tasks"][d]["status"] == "completed" for d in t["dependencies"])):
                t["status"] = "running"
                # Assign to idle subagent
                assigned = None
                for aid, a in self.agents.items():
                    if a["role"] == "subagent" and a["status"] == "idle":
                        assigned = aid
                        break
                if not assigned:
                    assigned = "AGENT-BACKEND-001"
                t["assigned_agent"] = assigned
                futures.append(self.executor.submit(self.execute_subagent, assigned, tid))

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

    def start_daemon_loop(self):
        daemon_info = {
            "pid": os.getpid(),
            "status": "running",
            "started_at": datetime.now().astimezone().isoformat(),
            "heartbeat_at": datetime.now().astimezone().isoformat()
        }
        self.save_state_atomic("daemon.json", daemon_info)
        self.log_event("daemon_started", f"Resident Orchestrator Daemon started with PID {os.getpid()}")

        try:
            while True:
                daemon_info["heartbeat_at"] = datetime.now().astimezone().isoformat()
                self.save_state_atomic("daemon.json", daemon_info)
                self.load_commands_from_queue()
                self.process_inbox()
                self.run_workflow_cycle()
                time.sleep(1)
        except KeyboardInterrupt:
            self.log_event("daemon_stopped", "Resident Orchestrator Daemon stopped manually.")
        finally:
            # Clean up daemon.json
            daemon_path = os.path.join(self.state_dir, "daemon.json")
            if os.path.exists(daemon_path):
                try:
                    os.remove(daemon_path)
                except Exception:
                    pass

if __name__ == "__main__":
    if "--daemon" in sys.argv:
        rt = HierarchicalRuntime("FEAT-112")
        rt.start_daemon_loop()
    else:
        rt = HierarchicalRuntime("FEAT-111")
        rt.receive_command("set concurrency 6")
        rt.process_inbox()
        rt.run_workflow_cycle()
        print("RUNTIME CYCLE EXECUTED SUCCESSFULLY")
