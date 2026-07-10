# worker_manager.py
"""
Worker PID tracker and registry for AIWF safe implementation orchestrator.
Manages workers.json with full lifecycle tracking.
Detects orphaned processes via PID liveness check.
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from atomic_writer import write_json_atomic, read_json_safe  # type: ignore

WORKERS_FILE = os.path.join(".agents", "runtime", "workers.json")
LOGS_DIR = os.path.join(".agents", "runtime", "logs")

# Worker status constants
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

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root
        if workspace_root:
            self._path = os.path.join(workspace_root, WORKERS_FILE)
            self._logs_dir = os.path.join(workspace_root, LOGS_DIR)
        else:
            self._path = WORKERS_FILE
            self._logs_dir = LOGS_DIR

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def register(
        self,
        task_id: str,
        pid: int,
        command: str,
        phase_id: str = "",
    ) -> str:
        """
        Register a new worker process.
        
        Args:
            task_id: ID of the task this worker is executing.
            pid: OS process ID of the worker.
            command: Command/description of what the worker is doing.
            phase_id: Optional phase this task belongs to.
        
        Returns:
            worker_id (str): UUID identifying this worker registration.
        """
        os.makedirs(self._logs_dir, exist_ok=True)
        worker_id = str(uuid.uuid4())
        log_file = os.path.join(self._logs_dir, f"{worker_id}.log")

        data = self._load()
        data["workers"][worker_id] = {
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
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save(data)
        return worker_id

    def mark_completed(self, worker_id: str) -> None:
        """Set worker status to 'completed' and record end time."""
        data = self._load()
        if worker_id in data["workers"]:
            data["workers"][worker_id]["status"] = WORKER_STATUS_COMPLETED
            data["workers"][worker_id]["ended_at"] = datetime.now(timezone.utc).isoformat()
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

    def mark_failed(self, worker_id: str, error: str = "") -> None:
        """Set worker status to 'failed' with error message."""
        data = self._load()
        if worker_id in data["workers"]:
            data["workers"][worker_id]["status"] = WORKER_STATUS_FAILED
            data["workers"][worker_id]["ended_at"] = datetime.now(timezone.utc).isoformat()
            data["workers"][worker_id]["error"] = error
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

    def detect_orphans(self) -> list[str]:
        """
        Return list of worker_ids where status is 'running' but PID is dead.
        Does NOT mark them as orphaned — caller decides what to do.
        """
        data = self._load()
        orphans = []
        for worker_id, wd in data["workers"].items():
            if wd.get("status") not in ACTIVE_STATUSES:
                continue
            pid = wd.get("pid")
            if not self._is_pid_alive(pid):
                orphans.append(worker_id)
        return orphans

    def mark_orphaned(self, worker_id: str) -> None:
        """Mark a worker as orphaned."""
        data = self._load()
        if worker_id in data["workers"]:
            data["workers"][worker_id]["status"] = WORKER_STATUS_ORPHANED
            data["workers"][worker_id]["ended_at"] = datetime.now(timezone.utc).isoformat()
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

    def terminate_orphan(self, worker_id: str, force: bool = False) -> bool:
        """
        Attempt to terminate an orphaned worker process.
        Sends SIGTERM first, then SIGKILL after 5s if force=True.
        
        Returns:
            True if worker was terminated successfully; False otherwise.
        """
        import signal
        import time

        data = self._load()
        wd = data["workers"].get(worker_id, {})
        pid = wd.get("pid")

        if pid is None:
            self.mark_orphaned(worker_id)
            return True  # No PID = already dead

        try:
            os.kill(int(pid), signal.SIGTERM)
            if force:
                time.sleep(5)
                if self._is_pid_alive(pid):
                    os.kill(int(pid), signal.SIGKILL)
        except (OSError, ProcessLookupError):
            pass  # Already dead

        self.mark_orphaned(worker_id)
        return True

    def get_active_workers(self) -> list[dict]:
        """Return all workers with status 'running' or 'starting'."""
        data = self._load()
        return [
            {"worker_id": wid, **wd}
            for wid, wd in data["workers"].items()
            if wd.get("status") in ACTIVE_STATUSES
        ]

    def has_active_workers(self) -> bool:
        """True if any worker has status 'running' or 'starting'."""
        return len(self.get_active_workers()) > 0

    def get_worker(self, worker_id: str) -> Optional[dict]:
        """Return worker record or None if not found."""
        data = self._load()
        return data["workers"].get(worker_id)

    def get_workers_for_task(self, task_id: str) -> list[dict]:
        """Return all workers associated with a task_id."""
        data = self._load()
        return [
            {"worker_id": wid, **wd}
            for wid, wd in data["workers"].items()
            if wd.get("task_id") == task_id
        ]

    def cleanup_completed(self, keep_failed: bool = True) -> int:
        """
        Remove completed workers from registry to keep file small.
        If keep_failed=True, failed workers are kept for debugging.
        Returns count of removed workers.
        """
        data = self._load()
        remove_statuses = {WORKER_STATUS_COMPLETED, WORKER_STATUS_ORPHANED}
        if not keep_failed:
            remove_statuses.add(WORKER_STATUS_FAILED)

        to_remove = [
            wid for wid, wd in data["workers"].items()
            if wd.get("status") in remove_statuses
        ]
        for wid in to_remove:
            del data["workers"][wid]

        if to_remove:
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)

        return len(to_remove)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        data = read_json_safe(self._path)
        if not isinstance(data, dict):
            return {
                "version": "1.0.0",
                "workers": {},
                "updated_at": "",
            }
        if "workers" not in data:
            data["workers"] = {}
        return data

    def _save(self, data: dict) -> None:
        parent = os.path.dirname(self._path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        write_json_atomic(self._path, data)

    def _is_pid_alive(self, pid) -> bool:
        """
        Check if a process is alive using os.kill(pid, 0).
        Returns False if PID is dead or invalid.
        """
        if pid is None:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except (OSError, ProcessLookupError, ValueError, TypeError):
            return False
