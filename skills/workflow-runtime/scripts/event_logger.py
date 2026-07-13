# event_logger.py
"""
Append-only event logger for AIWF runtime state.
Emits structured events to events/events.jsonl.
All event types are defined as string constants to allow validation.
"""
import os
import uuid
import threading
from datetime import datetime, timezone
from typing import Optional

from atomic_writer import append_jsonl, read_jsonl_safe  # type: ignore
from state_path import get_events_path  # type: ignore

# ---------------------------------------------------------------------------
# Event Type Constants
# ---------------------------------------------------------------------------
# Workflow lifecycle
WORKFLOW_INITIALIZED = "WorkflowInitialized"
SKILL_STARTED = "SkillStarted"
SKILL_COMPLETED = "SkillCompleted"
SKILL_FAILED = "SkillFailed"

# Phase and Task lifecycle
PHASE_STARTED = "PhaseStarted"
PHASE_COMPLETED = "PhaseCompleted"
TASK_STARTED = "TaskStarted"
TASK_COMPLETED = "TaskCompleted"
TASK_FAILED = "TaskFailed"

# Worker lifecycle
WORKER_SPAWNED = "WorkerSpawned"
WORKER_COMPLETED = "WorkerCompleted"
WORKER_FAILED = "WorkerFailed"
WORKER_ORPHANED = "WorkerOrphaned"

# File lock lifecycle
FILE_LOCK_ACQUIRED = "FileLockAcquired"
FILE_LOCK_RELEASED = "FileLockReleased"

# Quality gates
DEBUG_PASSED = "DebugPassed"
DEBUG_FAILED = "DebugFailed"
VERIFY_PASSED = "VerifyPassed"
VERIFY_FAILED = "VerifyFailed"

# Release lifecycle
RELEASE_REQUESTED = "ReleaseRequested"
RELEASE_BLOCKED = "ReleaseBlocked"
RELEASE_COMPLETED = "ReleaseCompleted"

# Usage & context
USAGE_UPDATED = "UsageUpdated"

# Recovery
STATE_MIGRATED = "StateMigrated"
STATE_DOCTOR_RUN = "StateDoctorRun"

# Gateway and trace events
WORKFLOW_REQUEST_RECEIVED = "workflow.request.received"
WORKFLOW_CREATED = "workflow.created"
WORKFLOW_STARTED_EVENT = "workflow.started"
WORKFLOW_PHASE_STARTED_EVENT = "workflow.phase.started"
SKILL_SELECTED = "skill.selected"
SKILL_STARTED_EVENT = "skill.started"
AGENT_STARTED = "agent.started"
TOOL_EXECUTED = "tool.executed"
ARTIFACT_CREATED = "artifact.created"
WORKFLOW_COMPLETED_EVENT = "workflow.completed"
WORKFLOW_ARTIFACT_VIOLATION = "workflow.artifact.violation"
WORKFLOW_BLOCKED = "workflow.blocked"

# All valid event types (used for validation)
ALL_EVENT_TYPES = frozenset([
    WORKFLOW_INITIALIZED, SKILL_STARTED, SKILL_COMPLETED, SKILL_FAILED,
    PHASE_STARTED, PHASE_COMPLETED, TASK_STARTED, TASK_COMPLETED, TASK_FAILED,
    WORKER_SPAWNED, WORKER_COMPLETED, WORKER_FAILED, WORKER_ORPHANED,
    FILE_LOCK_ACQUIRED, FILE_LOCK_RELEASED,
    DEBUG_PASSED, DEBUG_FAILED, VERIFY_PASSED, VERIFY_FAILED,
    RELEASE_REQUESTED, RELEASE_BLOCKED, RELEASE_COMPLETED,
    USAGE_UPDATED, STATE_MIGRATED, STATE_DOCTOR_RUN,
    WORKFLOW_REQUEST_RECEIVED, WORKFLOW_CREATED, WORKFLOW_STARTED_EVENT, WORKFLOW_PHASE_STARTED_EVENT,
    SKILL_SELECTED, SKILL_STARTED_EVENT, AGENT_STARTED, TOOL_EXECUTED,
    ARTIFACT_CREATED, WORKFLOW_COMPLETED_EVENT,
    WORKFLOW_ARTIFACT_VIOLATION, WORKFLOW_BLOCKED
])

# ---------------------------------------------------------------------------
# EventDeduplicateError
# ---------------------------------------------------------------------------

class EventDeduplicateError(ValueError):
    """Raised when an event with a duplicate event_id is emitted."""
    pass


# ---------------------------------------------------------------------------
# EventLogger
# ---------------------------------------------------------------------------

class EventLogger:
    """
    Thread-safe append-only event logger.
    Emits structured events to events/events.jsonl.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root
        self._emit_lock = threading.Lock()

    @property
    def events_path(self) -> str:
        return get_events_path(self._workspace_root)

    def emit(
        self,
        event_type: str,
        payload: dict,
        event_id: Optional[str] = None,
    ) -> str:
        """
        Create and append a structured event record to events.jsonl.
        
        Args:
            event_type: Must be one of the ALL_EVENT_TYPES constants.
            payload: Arbitrary dict describing the event.
            event_id: Optional UUID string. Auto-generated if not provided.
        
        Returns:
            event_id (str): The UUID of the emitted event.
        
        Raises:
            ValueError: If event_type is not a known constant.
            EventDeduplicateError: If event_id already exists in the log.
        """
        if event_type not in ALL_EVENT_TYPES:
            raise ValueError(
                f"Unknown event_type '{event_type}'. "
                f"Valid types: {sorted(ALL_EVENT_TYPES)}"
            )

        if event_id is None:
            event_id = str(uuid.uuid4())

        with self._emit_lock:
            # Lightweight duplicate check: look at last 20 events
            if self._is_duplicate(event_id, check_last_n=20):
                raise EventDeduplicateError(
                    f"Duplicate event_id '{event_id}' rejected."
                )

            record = {
                "event_id": event_id,
                "event_type": event_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }
            append_jsonl(self.events_path, record)

        return event_id

    def read_all(self) -> list[dict]:
        """
        Read all events from events.jsonl in chronological order.
        Invalid JSON lines are silently skipped.
        """
        return read_jsonl_safe(self.events_path)

    def compact(self, keep_last_n: int = 500) -> int:
        """
        Remove old events, keeping the last `keep_last_n` events.
        Writes compacted events back atomically.
        Returns number of events removed.
        """
        from atomic_writer import write_json_atomic  # type: ignore
        import json as _json

        with self._emit_lock:
            all_events = read_jsonl_safe(self.events_path)
            total = len(all_events)
            if total <= keep_last_n:
                return 0

            keep = all_events[-keep_last_n:]
            removed = total - len(keep)

            # Write compacted events back as JSONL
            lines = "\n".join(_json.dumps(e, ensure_ascii=False) for e in keep) + "\n"
            tmp_path = self.events_path + ".compact_tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(lines)

            import os
            os.replace(tmp_path, self.events_path)
            return removed

    def _is_duplicate(self, event_id: str, check_last_n: int = 20) -> bool:
        """Check if event_id exists in the last N events (lightweight dedup)."""
        all_events = read_jsonl_safe(self.events_path)
        recent = all_events[-check_last_n:] if len(all_events) > check_last_n else all_events
        return any(e.get("event_id") == event_id for e in recent)

    def get_last_event_of_type(self, event_type: str) -> Optional[dict]:
        """Return the most recent event of a given type, or None."""
        all_events = read_jsonl_safe(self.events_path)
        for event in reversed(all_events):
            if event.get("event_type") == event_type:
                return event
        return None

    def has_event(self, event_type: str) -> bool:
        """True if at least one event of this type exists."""
        return self.get_last_event_of_type(event_type) is not None

    def count_events(self, event_type: Optional[str] = None) -> int:
        """Count events of given type, or all events if type is None."""
        all_events = read_jsonl_safe(self.events_path)
        if event_type is None:
            return len(all_events)
        return sum(1 for e in all_events if e.get("event_type") == event_type)


# ---------------------------------------------------------------------------
# Module-level convenience functions (using default workspace)
# ---------------------------------------------------------------------------

_default_logger: Optional[EventLogger] = None
_logger_lock = threading.Lock()


def get_logger(workspace_root: Optional[str] = None) -> EventLogger:
    """Get the module-level default EventLogger singleton."""
    global _default_logger
    with _logger_lock:
        if _default_logger is None or (
            workspace_root and _default_logger._workspace_root != workspace_root
        ):
            _default_logger = EventLogger(workspace_root)
        return _default_logger


def emit_event(event_type: str, payload: dict, event_id: Optional[str] = None) -> str:
    """Convenience wrapper: emit event using default logger."""
    return get_logger().emit(event_type, payload, event_id)
