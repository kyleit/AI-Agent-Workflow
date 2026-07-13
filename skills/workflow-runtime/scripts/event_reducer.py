# event_reducer.py
"""
Event reducer for AIWF runtime state.
Routes events to handler functions that update canonical sub-state JSON files.
All handlers must be IDEMPOTENT — calling twice with the same event = same result.
"""
import os
from datetime import datetime, timezone
from typing import Optional

from atomic_writer import write_json_atomic, read_json_safe  # type: ignore
from state_path import get_state_file, get_subdir, ensure_dirs  # type: ignore
from event_logger import (  # type: ignore
    EventLogger, read_jsonl_safe,
    WORKFLOW_INITIALIZED, SKILL_STARTED, SKILL_COMPLETED, SKILL_FAILED,
    PHASE_STARTED, PHASE_COMPLETED, TASK_STARTED, TASK_COMPLETED, TASK_FAILED,
    WORKER_SPAWNED, WORKER_COMPLETED, WORKER_FAILED, WORKER_ORPHANED,
    FILE_LOCK_ACQUIRED, FILE_LOCK_RELEASED,
    DEBUG_PASSED, DEBUG_FAILED, VERIFY_PASSED, VERIFY_FAILED,
    RELEASE_REQUESTED, RELEASE_BLOCKED, RELEASE_COMPLETED,
    USAGE_UPDATED, STATE_MIGRATED,
    WORKFLOW_ARTIFACT_VIOLATION, WORKFLOW_BLOCKED
)


class EventReducer:
    """
    Routes incoming events to state-update handlers.
    Reads and writes canonical sub-state JSON files via AtomicWriter.
    Idempotent by design: applying same event twice = same final state.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root
        # Dispatch table: event_type -> handler method
        self._dispatch: dict = {
            WORKFLOW_INITIALIZED: self._on_workflow_initialized,
            SKILL_STARTED:        self._on_skill_started,
            SKILL_COMPLETED:      self._on_skill_completed,
            SKILL_FAILED:         self._on_skill_failed,
            PHASE_STARTED:        self._on_phase_started,
            PHASE_COMPLETED:      self._on_phase_completed,
            TASK_STARTED:         self._on_task_started,
            TASK_COMPLETED:       self._on_task_completed,
            TASK_FAILED:          self._on_task_failed,
            WORKER_SPAWNED:       self._on_worker_spawned,
            WORKER_COMPLETED:     self._on_worker_completed,
            WORKER_FAILED:        self._on_worker_failed,
            WORKER_ORPHANED:      self._on_worker_orphaned,
            FILE_LOCK_ACQUIRED:   self._on_file_lock_acquired,
            FILE_LOCK_RELEASED:   self._on_file_lock_released,
            DEBUG_PASSED:         self._on_debug_passed,
            DEBUG_FAILED:         self._on_debug_failed,
            VERIFY_PASSED:        self._on_verify_passed,
            VERIFY_FAILED:        self._on_verify_failed,
            RELEASE_REQUESTED:    self._on_release_requested,
            RELEASE_BLOCKED:      self._on_release_blocked,
            RELEASE_COMPLETED:    self._on_release_completed,
            USAGE_UPDATED:        self._on_usage_updated,
            STATE_MIGRATED:       self._on_state_migrated,
            WORKFLOW_ARTIFACT_VIOLATION: self._on_artifact_violation,
            WORKFLOW_BLOCKED:     self._on_workflow_blocked,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply(self, event: dict) -> None:
        """
        Dispatch a single event to its handler.
        Unknown event types are silently ignored (forward compatibility).
        """
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})
        handler = self._dispatch.get(event_type)
        if handler:
            handler(payload)

    def replay_all(self, events_path: Optional[str] = None) -> int:
        """
        Read all events from events.jsonl and replay them to rebuild state.
        Ensures directories exist before replaying.
        Returns number of events processed.
        """
        ensure_dirs(self._workspace_root)
        path = events_path or (
            EventLogger(self._workspace_root).events_path
        )
        events = read_jsonl_safe(path)
        for event in events:
            self.apply(event)
        return len(events)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, category: str) -> dict:
        """Read a sub-state JSON file. Return {} if missing or corrupt."""
        path = get_state_file(category, self._workspace_root)
        return read_json_safe(path) or {}

    def _write(self, category: str, data: dict) -> None:
        """Write a sub-state JSON file atomically."""
        path = get_state_file(category, self._workspace_root)
        write_json_atomic(path, data)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Workflow Handlers
    # ------------------------------------------------------------------

    def _on_workflow_initialized(self, p: dict) -> None:
        """Initialize workflow.json with baseline data."""
        existing = self._read("workflow")
        # Idempotent: only set if not already set (preserve later state)
        if existing.get("initialized_at"):
            return
        data = {
            "initialized_at": p.get("timestamp", self._now()),
            "feature_id": p.get("feature_id", ""),
            "current_skill": p.get("skill", "initialize-workflow"),
            "current_command": p.get("command", "init"),
            "current_step": p.get("step", ""),
            "checkpoint": p.get("checkpoint", 1),
            "suggested_next_skill": p.get("suggested_next_skill", "brainstorming"),
            "implementation_status": "not_started",
            "debug_status": "not_started",
            "verify_status": "not_started",
            "release_status": "not_started",
            "last_updated": self._now(),
        }
        self._write("workflow", data)

    def _on_skill_started(self, p: dict) -> None:
        """Update current_skill and current_step in workflow.json."""
        data = self._read("workflow")
        data["current_skill"] = p.get("skill", data.get("current_skill", ""))
        data["current_command"] = p.get("command", data.get("current_command", ""))
        data["current_step"] = p.get("step", "")
        data["checkpoint"] = p.get("checkpoint", data.get("checkpoint", 1))
        data["last_updated"] = self._now()
        self._write("workflow", data)

    def _on_skill_completed(self, p: dict) -> None:
        """Update workflow state on skill completion."""
        data = self._read("workflow")
        data["last_skill_completed"] = p.get("skill", "")
        data["suggested_next_skill"] = p.get("suggested_next_skill", "")
        data["last_updated"] = self._now()
        self._write("workflow", data)
        # Also update runtime.json
        runtime = self._read("runtime")
        runtime["last_skill_completed"] = p.get("skill", "")
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_skill_failed(self, p: dict) -> None:
        """Record skill failure in workflow.json."""
        data = self._read("workflow")
        data["last_skill_failed"] = p.get("skill", "")
        data["last_failure_reason"] = p.get("error", "")
        data["last_updated"] = self._now()
        self._write("workflow", data)

    # ------------------------------------------------------------------
    # Phase and Task Handlers
    # ------------------------------------------------------------------

    def _on_phase_started(self, p: dict) -> None:
        """Mark a phase as in_progress in runtime.json."""
        runtime = self._read("runtime")
        phases = runtime.setdefault("phases", {})
        phase_id = p.get("phase_id", "")
        if phase_id not in phases:
            phases[phase_id] = {
                "status": "in_progress",
                "started_at": self._now(),
                "completed_at": None,
            }
        else:
            # Idempotent: don't revert completed phase
            if phases[phase_id].get("status") != "completed":
                phases[phase_id]["status"] = "in_progress"
        runtime["current_phase"] = phase_id
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_phase_completed(self, p: dict) -> None:
        """Mark a phase as completed in runtime.json."""
        runtime = self._read("runtime")
        phases = runtime.setdefault("phases", {})
        phase_id = p.get("phase_id", "")
        phases[phase_id] = {
            "status": "completed",
            "started_at": phases.get(phase_id, {}).get("started_at"),
            "completed_at": self._now(),
        }
        runtime["last_phase_completed"] = phase_id
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_task_started(self, p: dict) -> None:
        """Mark a task as in_progress in runtime.json."""
        runtime = self._read("runtime")
        tasks = runtime.setdefault("tasks", {})
        task_id = p.get("task_id", "")
        if task_id not in tasks or tasks[task_id].get("status") != "completed":
            tasks[task_id] = {
                "status": "in_progress",
                "phase_id": p.get("phase_id", ""),
                "started_at": self._now(),
                "completed_at": None,
                "error": None,
            }
        runtime["current_task"] = task_id
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_task_completed(self, p: dict) -> None:
        """Mark a task as completed in runtime.json."""
        runtime = self._read("runtime")
        tasks = runtime.setdefault("tasks", {})
        task_id = p.get("task_id", "")
        existing = tasks.get(task_id, {})
        tasks[task_id] = {
            "status": "completed",
            "phase_id": p.get("phase_id", existing.get("phase_id", "")),
            "started_at": existing.get("started_at"),
            "completed_at": self._now(),
            "error": None,
        }
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_task_failed(self, p: dict) -> None:
        """Mark a task as failed and record error in runtime.json."""
        runtime = self._read("runtime")
        tasks = runtime.setdefault("tasks", {})
        task_id = p.get("task_id", "")
        existing = tasks.get(task_id, {})
        tasks[task_id] = {
            "status": "failed",
            "phase_id": p.get("phase_id", existing.get("phase_id", "")),
            "started_at": existing.get("started_at"),
            "completed_at": self._now(),
            "error": p.get("error", "Unknown error"),
        }
        runtime["last_task_failed"] = task_id
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    # ------------------------------------------------------------------
    # Worker Handlers
    # ------------------------------------------------------------------

    def _on_worker_spawned(self, p: dict) -> None:
        runtime = self._read("runtime")
        workers = runtime.setdefault("active_workers", {})
        worker_id = p.get("worker_id", "")
        workers[worker_id] = {
            "task_id": p.get("task_id", ""),
            "pid": p.get("pid"),
            "status": "running",
            "spawned_at": self._now(),
        }
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_worker_completed(self, p: dict) -> None:
        runtime = self._read("runtime")
        workers = runtime.setdefault("active_workers", {})
        worker_id = p.get("worker_id", "")
        if worker_id in workers:
            workers[worker_id]["status"] = "completed"
            workers[worker_id]["ended_at"] = self._now()
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_worker_failed(self, p: dict) -> None:
        runtime = self._read("runtime")
        workers = runtime.setdefault("active_workers", {})
        worker_id = p.get("worker_id", "")
        if worker_id in workers:
            workers[worker_id]["status"] = "failed"
            workers[worker_id]["error"] = p.get("error", "")
            workers[worker_id]["ended_at"] = self._now()
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_worker_orphaned(self, p: dict) -> None:
        runtime = self._read("runtime")
        workers = runtime.setdefault("active_workers", {})
        worker_id = p.get("worker_id", "")
        if worker_id in workers:
            workers[worker_id]["status"] = "orphaned"
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    # ------------------------------------------------------------------
    # Lock Handlers
    # ------------------------------------------------------------------

    def _on_file_lock_acquired(self, p: dict) -> None:
        runtime = self._read("runtime")
        locks = runtime.setdefault("active_locks", {})
        file_path = p.get("file_path", "")
        locks[file_path] = {
            "task_id": p.get("task_id", ""),
            "worker_id": p.get("worker_id", ""),
            "acquired_at": self._now(),
        }
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    def _on_file_lock_released(self, p: dict) -> None:
        runtime = self._read("runtime")
        locks = runtime.setdefault("active_locks", {})
        file_path = p.get("file_path", "")
        locks.pop(file_path, None)
        runtime["last_updated"] = self._now()
        self._write("runtime", runtime)

    # ------------------------------------------------------------------
    # Quality Gate Handlers
    # ------------------------------------------------------------------

    def _on_debug_passed(self, p: dict) -> None:
        workflow = self._read("workflow")
        workflow["debug_status"] = "pass"
        workflow["debug_passed_at"] = self._now()
        workflow["verify_allowed"] = True
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    def _on_debug_failed(self, p: dict) -> None:
        workflow = self._read("workflow")
        workflow["debug_status"] = "fail"
        workflow["verify_allowed"] = False
        workflow["release_allowed"] = False
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    def _on_verify_passed(self, p: dict) -> None:
        workflow = self._read("workflow")
        workflow["verify_status"] = "pass"
        workflow["verify_passed_at"] = self._now()
        workflow["release_allowed"] = True
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    def _on_verify_failed(self, p: dict) -> None:
        workflow = self._read("workflow")
        workflow["verify_status"] = "fail"
        workflow["release_allowed"] = False
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    # ------------------------------------------------------------------
    # Release Handlers
    # ------------------------------------------------------------------

    def _on_release_requested(self, p: dict) -> None:
        workflow = self._read("workflow")
        workflow["release_status"] = "requested"
        workflow["release_requested_at"] = self._now()
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    def _on_release_blocked(self, p: dict) -> None:
        workflow = self._read("workflow")
        workflow["release_status"] = "blocked"
        workflow["release_block_reason"] = p.get("reason", "")
        workflow["release_allowed"] = False
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    def _on_release_completed(self, p: dict) -> None:
        workflow = self._read("workflow")
        workflow["release_status"] = "completed"
        workflow["release_completed_at"] = self._now()
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    # ------------------------------------------------------------------
    # Misc Handlers
    # ------------------------------------------------------------------

    def _on_usage_updated(self, p: dict) -> None:
        """Update context/context.json with latest usage stats."""
        context = self._read("context")
        context.update(p)
        context["last_updated"] = self._now()
        self._write("context", context)

    def _on_state_migrated(self, p: dict) -> None:
        """Record migration event in recovery/recovery.json."""
        recovery_path = os.path.join(
            get_subdir("recovery", self._workspace_root), "recovery.json"
        )
        existing = read_json_safe(recovery_path) or {}
        existing["last_migration_at"] = self._now()
        existing["migration_details"] = p
        write_json_atomic(recovery_path, existing)

    def _on_artifact_violation(self, p: dict) -> None:
        """Record artifact governance violation in workflow.json."""
        workflow = self._read("workflow")
        workflow["status"] = "blocked"
        workflow["waiting_for"] = "Artifact governance violation"
        workflow["last_violation_reason"] = p.get("reason", "")
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)

    def _on_workflow_blocked(self, p: dict) -> None:
        """Mark workflow as blocked."""
        workflow = self._read("workflow")
        workflow["status"] = "blocked"
        workflow["waiting_for"] = p.get("reason", "Action required")
        workflow["last_updated"] = self._now()
        self._write("workflow", workflow)
