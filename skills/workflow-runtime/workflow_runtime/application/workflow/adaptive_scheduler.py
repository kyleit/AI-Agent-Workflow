# adaptive_scheduler.py
import json
import os
import time
from datetime import datetime
from typing import Any, Optional, Tuple, cast

import psutil

from workflow_runtime.application.ports.locator import InfrastructureLocator

# from workflow_runtime.infrastructure.execution.capacity_controller import CapacityController

class SchedulerMetrics:
    def __init__(self):
        self.planning_latency = 0.0
        self.execution_latency = 0.0
        self.merge_latency = 0.0
        self.conflict_rate = 0.0
        self.retry_rate = 0.0
        self.agent_utilization: dict[str, float] = {}
        self.token_usage = 0
        self.avg_cpu = 0.0
        self.avg_ram = 0.0
        self.throughput = 0.0

        self.total_tasks = 0
        self.completed_tasks = 0
        self.conflicts = 0
        self.retries = 0
        self.agent_busy_times: dict[str, float] = {}
        self.start_time = 0.0

    def start_execution(self):
        self.start_time = time.time()

    def end_execution(self):
        elapsed = time.time() - self.start_time
        self.execution_latency = elapsed
        if elapsed > 0:
            self.throughput = self.completed_tasks / elapsed

        # Hardware averages
        self.avg_cpu = psutil.cpu_percent()
        self.avg_ram = psutil.virtual_memory().percent

        # Calculate rates
        if self.total_tasks > 0:
            self.conflict_rate = self.conflicts / self.total_tasks
            self.retry_rate = self.retries / self.total_tasks

        # Agent utilization
        for aid, btime in self.agent_busy_times.items():
            self.agent_utilization[aid] = (btime / elapsed) if elapsed > 0 else 0.0

    def record_agent_busy(self, agent_id: str, duration: float):
        self.agent_busy_times[agent_id] = self.agent_busy_times.get(agent_id, 0.0) + duration

    def save_metrics(self, dest_path: str):
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        data = {
            "planning_latency_seconds": self.planning_latency,
            "execution_latency_seconds": self.execution_latency,
            "merge_latency_seconds": self.merge_latency,
            "conflict_rate": self.conflict_rate,
            "retry_rate": self.retry_rate,
            "agent_utilization": self.agent_utilization,
            "token_usage": self.token_usage,
            "avg_cpu_percent": self.avg_cpu,
            "avg_ram_percent": self.avg_ram,
            "throughput_tasks_per_sec": self.throughput
        }
        with open(dest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


class AdaptiveTeamPlanner:
    def __init__(self, token_budget: int = 100000):
        self.token_budget = token_budget
        self.roles_map = {
            "discovery": "AGENT-DISCOVERY-001",
            "planning": "AGENT-PM-001",
            "blueprint": "AGENT-ARCH-001",
            "development": "AGENT-BACKEND-001",
            "frontend": "AGENT-FRONTEND-001",
            "test": "AGENT-TEST-001",
            "debug": "AGENT-DEBUG-001",
            "verification": "AGENT-VERIFY-001",
        }

    def determine_execution_mode(self, task_name: str, locks: list[str]) -> str:
        lower_name = task_name.lower()

        # Mode A: Git/release/bump tasks
        is_mode_a = any(k in lower_name for k in ["release", "changelog", "bump", "git", "commit", "tag", "push"])
        is_mode_a = is_mode_a or any("AI_RULES" in l or "AGENTS" in l for l in locks)

        if is_mode_a:
            return "A"

        # Mode C: Isolated write scopes (e.g. backend implementation)
        has_isolated_locks = len(locks) > 0 and all(
            any(isolated in l for isolated in ["backend/", "frontend/", "tests/", "designs/", "verification/"])
            for l in locks
        )
        if has_isolated_locks and any(p in lower_name for p in ["implementation", "dashboard", "updates", "test"]):
            return "C"

        # Mode B: Fallback research/planning
        return "B"

    def plan_team_and_graph(self, work_item_id: str, raw_tasks: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any], float]:
        tstart = time.time()

        # 1. Dynamically spawn required agents based on task roles needed
        required_roles: set[str] = set()
        for rt in raw_tasks:
            role = str(rt.get("role", "development"))
            required_roles.add(role)

        agents: dict[str, Any] = {}
        for role in required_roles:
            agent_id = self.roles_map.get(role, f"AGENT-{role.upper()}-001")
            agents[agent_id] = {
                "id": agent_id,
                "name": f"{role.capitalize()} Agent",
                "role": role,
                "status": "IDLE",
                "heartbeat": time.time(),
                "retry_count": 0,
                "capabilities": [f"{role} execution"],
                "last_active": time.time()
            }

        # 2. Build Dependency Graph DAG
        tasks_graph: dict[str, Any] = {}
        for idx, rt in enumerate(raw_tasks):
            tid = f"TASK-{idx+1:03d}"
            locks = cast(list[str], rt.get("locks", []))
            mode = self.determine_execution_mode(str(rt.get("name", "")), locks)
            role = str(rt.get("role", "development"))
            assigned_agent = self.roles_map.get(role, "AGENT-BACKEND-001")

            # Estimate token allocation per task
            task_tokens = 2000
            if mode == "B":
                task_tokens = 5000
            elif mode == "C":
                task_tokens = 8000

            tasks_graph[tid] = {
                "id": tid,
                "name": rt.get("name", ""),
                "dependencies": rt.get("dependencies", []),
                "status": "pending",
                "assigned_agent": assigned_agent,
                "role": role,
                "locks": locks,
                "required": True,
                "mode": mode,
                "allocated_tokens": task_tokens
            }

        # Calculate dynamic dependencies if not specified
        for i in range(1, len(raw_tasks) + 1):
            tid = f"TASK-{i:03d}"
            t = cast(dict[str, Any], tasks_graph[tid])
            if not t.get("dependencies") and i > 1:
                t["dependencies"] = [f"TASK-{i-1:03d}"]

        graph: dict[str, Any] = {
            "graph_id": f"GRAPH-{work_item_id}",
            "tasks": tasks_graph
        }

        planning_latency = time.time() - tstart
        return agents, graph, planning_latency


class RuntimeScheduler:
    def __init__(self, agents: dict[str, Any], graph: dict[str, Any], metrics: SchedulerMetrics, policy: dict[str, Any] | None = None):
        self.agents = agents
        self.graph = graph
        self.metrics = metrics
        self.metrics.total_tasks = len(graph["tasks"])
        self.active_locks: dict[str, dict[str, Any]] = {}
        self.worktrees: dict[str, str] = {}

        p = policy or {}
        self.max_runtime_managers_per_workspace = p.get("max_runtime_managers_per_workspace", 1)
        self.max_orchestrators_per_workspace = p.get("max_orchestrators_per_workspace", 1)
        self.max_python_worker_processes = p.get("max_python_worker_processes", 4)
        self.max_logical_agents = p.get("max_logical_agents", 10)
        self.max_concurrent_tasks = p.get("max_concurrent_tasks", 4)

        # Resources limits
        self.max_memory_mb = p.get("max_memory_mb", 2048)
        self.max_cpu_percent = p.get("max_cpu_percent", 80.0)
        self.worker_idle_ttl_seconds = p.get("worker_idle_ttl_seconds", 10.0)
        self.worker_shutdown_grace_seconds = p.get("worker_shutdown_grace_seconds", 2.0)

        # Spawn settings
        self.spawn_timestamps: list[float] = []
        self.spawn_rate_limit = p.get("spawn_rate_limit", 10)
        self.max_spawn_retries = p.get("max_spawn_retries", 3)
        self.active_processes: dict[str, Any] = {}

        # Centralized Capacity Controller integration
        self.capacity_controller = InfrastructureLocator.CapacityController(
            max_cpu_percent=self.max_cpu_percent,
            max_ram_percent=85.0,
            max_concurrency=self.max_concurrent_tasks
        )
        self.recruitment_decisions: list[dict[str, Any]] = []

    def check_spawn_rate_limit(self) -> bool:
        now = time.time()
        self.spawn_timestamps = [t for t in self.spawn_timestamps if now - t < 60]
        if len(self.spawn_timestamps) >= self.spawn_rate_limit:
            return False
        self.spawn_timestamps.append(now)
        return True

    def scale_agents(self) -> int:
        # Utilize central Capacity Controller evaluation
        concurrency = self.capacity_controller.evaluate_concurrency_limit()
        return min(concurrency, self.max_python_worker_processes)

    def recruit_dynamic(self, role: str, workload_size: int) -> Tuple[bool, str]:
        # Recruitment validation under hardware constraints
        allowed, msg = self.capacity_controller.can_recruit(role, workload_size)
        if not allowed:
            self.recruitment_decisions.append({
                "role": role,
                "status": "rejected",
                "reason": msg,
                "timestamp": datetime.now().astimezone().isoformat()
            })
            return False, msg

        # Spawn Dynamic Specialist Agent
        agent_id = f"AGENT-DYNAMIC-{role.upper()}-{len(self.agents) + 1:03d}"
        self.agents[agent_id] = {
            "id": agent_id,
            "name": f"Dynamic {role.capitalize()} Specialist",
            "role": role,
            "status": "IDLE",
            "heartbeat": time.time(),
            "retry_count": 0,
            "capabilities": [f"{role} execution"],
            "last_active": time.time()
        }
        self.capacity_controller.recruit_agent(agent_id, role)
        self.recruitment_decisions.append({
            "agent_id": agent_id,
            "role": role,
            "status": "recruited",
            "timestamp": datetime.now().astimezone().isoformat()
        })
        return True, agent_id

    def reclaim_idle_agents(self, idle_timeout: Optional[float] = None):
        reclaimed_ids = self.capacity_controller.reclaim_idle_agents(self.agents, idle_timeout)
        for aid in reclaimed_ids:
            if aid in self.agents:
                del self.agents[aid]
                self.capacity_controller.release_agent(aid)
        return reclaimed_ids

    def check_lease_overlap(self, path1: str, path2: str) -> bool:
        p1 = os.path.normpath(path1).replace("\\", "/").rstrip("/")
        p2 = os.path.normpath(path2).replace("\\", "/").rstrip("/")
        return p1.startswith(p2 + "/") or p2.startswith(p1 + "/") or p1 == p2

    def acquire_leases(self, task_id: str, agent_id: str, locks: list[str]) -> bool:
        for resource in locks:
            for locked_res, owner in list(self.active_locks.items()):
                if self.check_lease_overlap(locked_res, resource):
                    if owner.get("agent_id") != agent_id:
                        return False

        for resource in locks:
            self.active_locks[resource] = {
                "agent_id": agent_id,
                "task_id": task_id,
                "acquired_at": datetime.now().astimezone().isoformat()
            }
        return True

    def release_leases(self, agent_id: str):
        for resource, owner in list(self.active_locks.items()):
            if owner.get("agent_id") == agent_id:
                del self.active_locks[resource]

    def execute_task(self, task_id: str, simulate_lock_conflict: bool = False, simulate_retry: bool = False) -> bool:
        tasks_map = cast(dict[str, Any], self.graph.get("tasks", {}))
        t = cast(dict[str, Any], tasks_map[task_id])
        agent_id = t["assigned_agent"]
        mode = t.get("mode", "A")

        # Enforce Logical Agent budget
        active_agents = [aid for aid, a in self.agents.items() if isinstance(a, dict) and cast(dict[str, Any], a).get("status") == "ACTIVE"]
        if agent_id not in active_agents and len(active_agents) >= self.max_logical_agents:
            t["status"] = "blocked"
            return False

        # Enforce OS Process budget for Mode C tasks
        if mode == "C":
            if len(self.active_processes) >= self.max_python_worker_processes:
                t["status"] = "blocked"
                return False

        # Recreate agent if dynamically destroyed earlier
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "id": agent_id,
                "name": f"Dynamic Agent",
                "role": t["role"],
                "status": "IDLE",
                "heartbeat": time.time(),
                "retry_count": 0,
                "capabilities": [f"{t['role']} execution"],
                "last_active": time.time()
            }

        agent = cast(dict[str, Any], self.agents[agent_id])
        agent["status"] = "ACTIVE"
        agent["last_active"] = time.time()
        t["status"] = "running"

        tstart = time.time()
        if simulate_lock_conflict or not self.acquire_leases(task_id, agent_id, t["locks"]):
            self.metrics.conflicts += 1
            t["status"] = "blocked"
            t["attempt"] = t.get("attempt", 0) + 1
            agent["status"] = "IDLE"
            agent["last_active"] = time.time()
            return False

        # Simulate Execution
        execution_time = 0.05
        if mode == "C":
            self.active_processes[task_id] = {
                "pid": 1000 + len(self.active_processes),
                "ram_mb": 80,
                "started_at": time.time()
            }
            self.worktrees[task_id] = f"git-worktree-{task_id}"
            execution_time = 0.1
        elif mode == "B":
            execution_time = 0.08

        if simulate_retry:
            self.metrics.retries += 1
            t["attempt"] = t.get("attempt", 0) + 1
            self.release_leases(agent_id)
            if mode == "C" and task_id in self.active_processes:
                del self.active_processes[task_id]
            t["status"] = "failed"
            agent["status"] = "IDLE"
            agent["last_active"] = time.time()
            return False

        time.sleep(execution_time)

        self.release_leases(agent_id)
        if mode == "C" and task_id in self.active_processes:
            del self.active_processes[task_id]
        t["status"] = "completed"
        agent["status"] = "IDLE"
        agent["last_active"] = time.time()

        duration = time.time() - tstart
        self.metrics.record_agent_busy(agent_id, duration)
        self.metrics.completed_tasks += 1
        self.metrics.token_usage += t.get("allocated_tokens", 2000)

        return True

    def execute_graph(self, lock_conflict_idx: int = -1, retry_idx: int = -1, force_tasks: list[str] | None = None) -> None:
        self.metrics.start_execution()
        tasks_map = cast(dict[str, Any], self.graph.get("tasks", {}))
        pending = list(tasks_map.keys())

        # Build priority queue: Force Tasks bypass queue order (scheduled first)
        force_queue = force_tasks or []

        while pending:
            max_workers = self.scale_agents()

            # 1. Identify ready tasks whose dependencies are completed
            ready: list[str] = []
            for tid in pending:
                t = cast(dict[str, Any], tasks_map[tid])
                deps = cast(list[str], t.get("dependencies", []))
                deps_ok = all(cast(dict[str, Any], tasks_map.get(dep, {})).get("status") == "completed" for dep in deps)
                if deps_ok and t.get("status") not in ["running", "completed"]:
                    ready.append(tid)

            if not ready:
                break

            # 2. Sort ready tasks so that Force Tasks are executed first
            ready_sorted: list[str] = []
            for ft in force_queue:
                if ft in ready:
                    ready_sorted.append(ft)
            for r in ready:
                if r not in ready_sorted:
                    ready_sorted.append(r)

            dispatched = 0
            for tid in ready_sorted:
                if dispatched >= max_workers:
                    break

                # Check dynamic recruitment trigger if workload is medium/large
                target_task = cast(dict[str, Any], tasks_map[tid])
                role = str(target_task.get("role", "development"))
                idle_agents = [aid for aid, a in self.agents.items() if isinstance(a, dict) and cast(dict[str, Any], a).get("status") == "IDLE" and cast(dict[str, Any], a).get("role") == role]

                # Dynamic recruitment policy (recruit if no idle agent of matching role exists)
                if not idle_agents:
                    success_rec, rec_res = self.recruit_dynamic(role, len(pending))
                    if success_rec:
                        target_task["assigned_agent"] = rec_res

                idx = int(tid.split("-")[-1])
                sim_conflict = (idx == lock_conflict_idx and target_task.get("attempt", 0) == 0)
                sim_retry = (idx == retry_idx and target_task.get("attempt", 0) == 0)

                success = self.execute_task(tid, simulate_lock_conflict=sim_conflict, simulate_retry=sim_retry)
                if success:
                    pending.remove(tid)
                    dispatched += 1
                else:
                    if target_task.get("status") == "failed":
                        target_task["status"] = "queued"
                    elif target_task.get("status") == "blocked":
                        target_task["status"] = "ready"
                    dispatched += 1

            self.reclaim_idle_agents()
            time.sleep(0.01)

        self.metrics.end_execution()
