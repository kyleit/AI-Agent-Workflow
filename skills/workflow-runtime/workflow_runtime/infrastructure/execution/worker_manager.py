from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, cast

from workflow_runtime.infrastructure.filesystem.atomic_writer import (
    read_json_safe, write_json_atomic)

WORKERS_FILE = os.path.join(".agents", "runtime", "workers.json")
LOGS_DIR = os.path.join(".agents", "runtime", "logs")

WORKER_STATUS_STARTING = "starting"
WORKER_STATUS_RUNNING = "running"
WORKER_STATUS_COMPLETED = "completed"
WORKER_STATUS_FAILED = "failed"
WORKER_STATUS_ORPHANED = "orphaned"

ACTIVE_STATUSES = frozenset([WORKER_STATUS_STARTING, WORKER_STATUS_RUNNING])


class WorkerManager:
    """
    Registry for worker processes spawned during implementation.
    Provides orphan detection via PID liveness check (os.kill(pid, 0)).
    Per-worker log files stored in .agents/runtime/logs/.
    """

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        self._workspace_root = workspace_root
        if workspace_root:
            self._path = os.path.join(workspace_root, WORKERS_FILE)
            self._logs_dir = os.path.join(workspace_root, LOGS_DIR)
        else:
            self._path = WORKERS_FILE
            self._logs_dir = LOGS_DIR

    def register(
        self,
        task_id: str,
        pid: int,
        command: str,
        phase_id: str = "",
    ) -> str:
        os.makedirs(self._logs_dir, exist_ok=True)
        worker_id = str(uuid.uuid4())
        log_file = os.path.join(self._logs_dir, f"{worker_id}.log")

        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        workers[worker_id] = {
            "task_id": task_id,
            "phase_id": phase_id,
            "pid": pid,
            "status": WORKER_STATUS_RUNNING,
            "command": command,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "ended_at": None,
            "log_file": log_file,
            "error": None,
        }
        data["workers"] = workers
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save(data)
        return worker_id

    def mark_completed(self, worker_id: str) -> None:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        if worker_id in workers:
            wentry = cast(dict[str, Any], workers[worker_id]) if isinstance(workers[worker_id], dict) else {}
            wentry["status"] = WORKER_STATUS_COMPLETED
            wentry["ended_at"] = datetime.now(timezone.utc).isoformat()
            workers[worker_id] = wentry
            data["workers"] = workers
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

    def mark_failed(self, worker_id: str, error: str = "") -> None:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        if worker_id in workers:
            wentry = cast(dict[str, Any], workers[worker_id]) if isinstance(workers[worker_id], dict) else {}
            wentry["status"] = WORKER_STATUS_FAILED
            wentry["ended_at"] = datetime.now(timezone.utc).isoformat()
            wentry["error"] = error
            workers[worker_id] = wentry
            data["workers"] = workers
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

    def detect_orphans(self) -> list[str]:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        orphans: list[str] = []
        for worker_id, wd in workers.items():
            wd_dict = cast(dict[str, Any], wd) if isinstance(wd, dict) else {}
            if str(wd_dict.get("status", "")) not in ACTIVE_STATUSES:
                continue
            pid = wd_dict.get("pid")
            if not self._is_pid_alive(pid):
                orphans.append(worker_id)
        return orphans

    def mark_orphaned(self, worker_id: str) -> None:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        if worker_id in workers:
            wentry = cast(dict[str, Any], workers[worker_id]) if isinstance(workers[worker_id], dict) else {}
            wentry["status"] = WORKER_STATUS_ORPHANED
            wentry["ended_at"] = datetime.now(timezone.utc).isoformat()
            workers[worker_id] = wentry
            data["workers"] = workers
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

    def terminate_orphan(self, worker_id: str, force: bool = False) -> bool:
        import signal
        import time

        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        wd = cast(dict[str, Any], workers.get(worker_id, {})) if isinstance(workers.get(worker_id), dict) else {}
        pid = wd.get("pid")

        if pid is None:
            self.mark_orphaned(worker_id)
            return True

        try:
            os.kill(int(str(pid)), signal.SIGTERM)
            if force:
                time.sleep(5)
                if self._is_pid_alive(pid):
                    sig_kill = getattr(signal, "SIGKILL", signal.SIGTERM)
                    os.kill(int(str(pid)), sig_kill)
        except (OSError, ProcessLookupError, ValueError, TypeError):
            pass

        self.mark_orphaned(worker_id)
        return True

    def get_active_workers(self) -> list[dict[str, Any]]:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        return [
            {"worker_id": wid, **cast(dict[str, Any], wd)}
            for wid, wd in workers.items()
            if isinstance(wd, dict) and str(cast(dict[str, Any], wd).get("status", "")) in ACTIVE_STATUSES
        ]

    def has_active_workers(self) -> bool:
        return len(self.get_active_workers()) > 0

    def get_worker(self, worker_id: str) -> dict[str, Any] | None:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        item = workers.get(worker_id)
        return cast(dict[str, Any], item) if isinstance(item, dict) else None

    def get_workers_for_task(self, task_id: str) -> list[dict[str, Any]]:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        return [
            {"worker_id": wid, **cast(dict[str, Any], wd)}
            for wid, wd in workers.items()
            if isinstance(wd, dict) and str(cast(dict[str, Any], wd).get("task_id", "")) == task_id
        ]

    def cleanup_completed(self, keep_failed: bool = True) -> int:
        data = self._load()
        raw_workers = data.get("workers")
        workers: dict[str, Any] = cast(dict[str, Any], raw_workers) if isinstance(raw_workers, dict) else {}
        remove_statuses = {WORKER_STATUS_COMPLETED, WORKER_STATUS_ORPHANED}
        if not keep_failed:
            remove_statuses.add(WORKER_STATUS_FAILED)

        to_remove = [
            wid for wid, wd in workers.items()
            if isinstance(wd, dict) and str(cast(dict[str, Any], wd).get("status", "")) in remove_statuses
        ]
        for wid in to_remove:
            if wid in workers:
                del workers[wid]

        if to_remove:
            data["workers"] = workers
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

        return len(to_remove)

    def _load(self) -> dict[str, Any]:
        data = read_json_safe(self._path)
        if not isinstance(data, dict):
            return {
                "version": "1.0.0",
                "workers": {},
                "updated_at": "",
            }
        raw_dict = cast(dict[str, Any], data)
        raw_w: Any = raw_dict.get("workers")
        if "workers" not in raw_dict or not isinstance(raw_w, dict):
            raw_dict["workers"] = {}
        return raw_dict

    def _save(self, data: dict[str, Any]) -> None:
        parent = os.path.dirname(self._path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        write_json_atomic(self._path, data)

    def _is_pid_alive(self, pid: Any) -> bool:
        if pid is None:
            return False
        try:
            os.kill(int(str(pid)), 0)
            return True
        except (OSError, ProcessLookupError, ValueError, TypeError):
            return False


__all__ = [
    "WORKER_STATUS_STARTING",
    "WORKER_STATUS_RUNNING",
    "WORKER_STATUS_COMPLETED",
    "WORKER_STATUS_FAILED",
    "WORKER_STATUS_ORPHANED",
    "ACTIVE_STATUSES",
    "WorkerManager",
]
