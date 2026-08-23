from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

# logical_scheduler.py


class TaskTransitionError(Exception):
    pass


class Task:
    def __init__(
        self,
        task_id: str,
        session_id: str,
        agent_id: str,
        priority: str = "medium",
        dependencies: list[str] | None = None,
        requirements: dict[str, Any] | None = None,
        resource_estimate: dict[str, Any] | None = None,
        retry_policy: dict[str, Any] | None = None
    ) -> None:
        self.task_id = task_id
        self.session_id = session_id
        self.agent_id = agent_id
        self.priority = priority
        self.dependencies: list[str] = dependencies or []
        self.requirements: dict[str, Any] = requirements or {}
        self.resource_estimate: dict[str, Any] = resource_estimate or {"cpu": 1, "ram_mb": 50}
        self.retry_policy: dict[str, Any] = retry_policy or {"max_retries": 3}

        self.status = "created"
        self.created_at = datetime.now().astimezone().isoformat()
        self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "status": self.status,
            "requirements": self.requirements,
            "resource_estimate": self.resource_estimate,
            "retry_policy": self.retry_policy,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def transition_to(self, target_status: str, event_store: Any | None = None) -> None:
        VALID_TRANSITIONS: dict[str, list[str]] = {
            "created": ["queued", "cancelled", "failed"],
            "queued": ["scheduled", "cancelled", "failed"],
            "scheduled": ["running", "cancelled", "failed"],
            "running": ["completed", "failed", "cancelled", "retrying", "blocked"],
            "waiting": ["running", "cancelled", "failed"],
            "blocked": ["queued", "cancelled", "failed"],
            "retrying": ["queued", "cancelled", "failed"],
            "completed": [],
            "failed": [],
            "cancelled": []
        }

        allowed = VALID_TRANSITIONS.get(self.status, [])
        if target_status not in allowed:
            raise TaskTransitionError(
                f"Invalid transition for task '{self.task_id}': cannot move from '{self.status}' to '{target_status}'."
            )

        self.status = target_status
        self.updated_at = datetime.now().astimezone().isoformat()

        if event_store:
            append_fn: Any = getattr(event_store, "append_event", None)
            if callable(append_fn):
                append_fn(
                    session_id=self.session_id,
                    topic="task.transitioned",
                    payload={
                        "task_id": self.task_id,
                        "status": self.status,
                        "updated_at": self.updated_at
                    }
                )


class Worker:
    def __init__(self, worker_id: str, pool_executor: BoundedWorkerPool) -> None:
        self.worker_id = worker_id
        self.pool_executor = pool_executor
        self.status = "idle"
        self.assigned_task_id: str | None = None
        self.is_healthy = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker_id": self.worker_id,
            "status": self.status,
            "assigned_task_id": self.assigned_task_id,
            "is_healthy": self.is_healthy
        }


class BoundedWorkerPool:
    def __init__(
        self,
        session_id: str,
        max_workers: int = 4,
        event_store: Any | None = None
    ) -> None:
        self.session_id = session_id
        self.max_workers = max_workers
        self.event_store = event_store

        self.workers: dict[str, Worker] = {}
        self._lock = asyncio.Lock()
        self.status = "active"

        for i in range(max_workers):
            w_id = f"worker-{i}"
            worker = Worker(worker_id=w_id, pool_executor=self)
            worker.status = "idle"
            self.workers[w_id] = worker

            if self.event_store:
                append_fn: Any = getattr(self.event_store, "append_event", None)
                if callable(append_fn):
                    append_fn(
                        session_id=self.session_id,
                        topic="worker.created",
                        payload=worker.to_dict()
                    )

    async def get_idle_worker(self) -> Worker | None:
        async with self._lock:
            if self.status != "active":
                return None
            for w in self.workers.values():
                if w.status == "idle" and w.is_healthy:
                    return w
            return None

    async def assign_worker(self, worker_id: str, task_id: str) -> None:
        async with self._lock:
            worker = self.workers[worker_id]
            worker.status = "assigned"
            worker.assigned_task_id = task_id

            if self.event_store:
                append_fn: Any = getattr(self.event_store, "append_event", None)
                if callable(append_fn):
                    append_fn(
                        session_id=self.session_id,
                        topic="worker.assigned",
                        payload=worker.to_dict()
                    )

    async def release_worker(self, worker_id: str, mark_unhealthy: bool = False) -> None:
        async with self._lock:
            if worker_id not in self.workers:
                return
            worker = self.workers[worker_id]
            worker.status = "idle"
            worker.assigned_task_id = None
            if mark_unhealthy:
                worker.is_healthy = False

            if self.event_store:
                append_fn: Any = getattr(self.event_store, "append_event", None)
                if callable(append_fn):
                    append_fn(
                        session_id=self.session_id,
                        topic="worker.released",
                        payload=worker.to_dict()
                    )
                    if mark_unhealthy:
                        append_fn(
                            session_id=self.session_id,
                            topic="worker.failed",
                            payload={"worker_id": worker_id, "reason": "unhealthy flag set"}
                        )

    async def shutdown(self) -> None:
        async with self._lock:
            self.status = "shutdown"
            self.workers.clear()


class LogicalScheduler:
    def __init__(
        self,
        session_id: str,
        worker_pool: BoundedWorkerPool,
        queue_limit: int = 100,
        event_store: Any | None = None
    ) -> None:
        self.session_id = session_id
        self.worker_pool = worker_pool
        self.queue_limit = queue_limit
        self.event_store = event_store

        self.tasks: dict[str, Task] = {}
        self.queue: list[str] = []
        self._lock = asyncio.Lock()

        self.cpu_throttle_limit = 90.0
        self.ram_watermark_limit = 80.0
        self.mock_cpu_usage = 45.0
        self.mock_ram_usage = 55.0

    async def submit_task(self, task: Task) -> str:
        async with self._lock:
            if len(self.queue) >= self.queue_limit:
                if self.event_store:
                    append_fn: Any = getattr(self.event_store, "append_event", None)
                    if callable(append_fn):
                        append_fn(
                            session_id=self.session_id,
                            topic="scheduler.throttled",
                            payload={"reason": "queue limit exceeded"}
                        )
                raise ResourceWarning("Scheduler backpressure: Queue limit exceeded.")

            self.tasks[task.task_id] = task
            self.queue.append(task.task_id)
            task.transition_to("queued", self.event_store)
            return task.task_id

    async def dispatch_next(self) -> tuple[Task, Worker] | None:
        async with self._lock:
            if self.mock_cpu_usage > self.cpu_throttle_limit or self.mock_ram_usage > self.ram_watermark_limit:
                if self.event_store:
                    append_fn: Any = getattr(self.event_store, "append_event", None)
                    if callable(append_fn):
                        append_fn(
                            session_id=self.session_id,
                            topic="scheduler.throttled",
                            payload={"cpu": self.mock_cpu_usage, "ram": self.mock_ram_usage}
                        )
                return None

            schedulable_task_id: str | None = None
            for t_id in self.queue:
                task = self.tasks[t_id]
                if task.status == "queued":
                    deps_satisfied = True
                    for dep_id in task.dependencies:
                        dep_task = self.tasks.get(dep_id)
                        if not dep_task or dep_task.status != "completed":
                            deps_satisfied = False
                            break
                    if deps_satisfied:
                        if not schedulable_task_id:
                            schedulable_task_id = t_id
                        else:
                            curr_t = self.tasks[schedulable_task_id]
                            prios = {"high": 3, "medium": 2, "low": 1}
                            if prios.get(task.priority, 2) > prios.get(curr_t.priority, 2):
                                schedulable_task_id = t_id

            if not schedulable_task_id:
                return None

            worker = await self.worker_pool.get_idle_worker()
            if not worker:
                return None

            task = self.tasks[schedulable_task_id]
            task.transition_to("scheduled", self.event_store)
            await self.worker_pool.assign_worker(worker.worker_id, task.task_id)

            return task, worker

    async def execute_task_simulated(self, task_id: str, worker_id: str) -> None:
        task = self.tasks[task_id]
        task.transition_to("running", self.event_store)

        await asyncio.sleep(0.01)

        task.transition_to("completed", self.event_store)
        await self.worker_pool.release_worker(worker_id)


__all__ = [
    "TaskTransitionError",
    "Task",
    "Worker",
    "BoundedWorkerPool",
    "LogicalScheduler",
]
