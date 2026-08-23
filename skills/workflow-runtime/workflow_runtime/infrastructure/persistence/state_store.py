from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from workflow_runtime.domain.workflow.entities import Checkpoint, WorkflowState
from workflow_runtime.domain.workflow.repositories import IWorkflowRepository
from workflow_runtime.domain.workflow.value_objects import PhaseStatus, RoleId
from workflow_runtime.shared.errors import (EntityNotFoundError,
                                            RevisionConflictError)
from workflow_runtime.shared.utils import atomic_write_json

# ---------------------------------------------------------------------------
# Legacy status coercion map
# Older versions of the framework (or custom skill authors) may have written
# non-standard status strings into workflow.json / checkpoints.json.
# Map known legacy values to their canonical equivalents before enum parsing.
# ---------------------------------------------------------------------------
_LEGACY_STATUS_MAP: dict[str, str] = {
    # Completion variants
    "FEATURE_IMPLEMENTATION_COMPLETED": "COMPLETED",
    "IMPLEMENTATION_COMPLETED": "COMPLETED",
    "DONE": "COMPLETED",
    "SUCCESS": "COMPLETED",
    "PASSED": "COMPLETED",
    # In-progress variants
    "RUNNING": "IN_PROGRESS",
    "ACTIVE": "IN_PROGRESS",
    "EXECUTING": "IN_PROGRESS",
    "STARTED": "IN_PROGRESS",
    # Failure variants
    "ERROR": "FAILED",
    "ABORTED": "FAILED",
    "CANCELLED": "FAILED",
    # Blocked variants
    "WAITING": "BLOCKED",
    "PAUSED": "BLOCKED",
    "ON_HOLD": "BLOCKED",
}


def _coerce_phase_status(raw: str, default: str = "IN_PROGRESS") -> PhaseStatus:
    """Parse a PhaseStatus from a raw string with legacy value coercion.

    If the raw value is not a valid PhaseStatus member, it is checked against
    the legacy map. Unknown values fall back to `default` rather than crashing.
    """
    if not raw:
        return PhaseStatus(default)
    normalized = raw.strip().upper()
    # Try direct parse first
    try:
        return PhaseStatus(normalized)
    except ValueError:
        pass
    # Try legacy map
    mapped = _LEGACY_STATUS_MAP.get(normalized)
    if mapped:
        return PhaseStatus(mapped)
    # Last resort: return default
    return PhaseStatus(default)


def _rel_path_str(path: Path) -> str:
    try:
        return os.path.relpath(str(path))
    except ValueError:
        return str(path)


class StateStoreAdapter(IWorkflowRepository):
    """Adapter for split-state JSON persistence under .agents/state/."""

    def __init__(self, state_root: str = ".agents/state") -> None:
        self._state_root = Path(state_root)
        self._state_root.mkdir(parents=True, exist_ok=True)

    def get_state(self, session_id: str = "default") -> WorkflowState:
        """Retrieves the current WorkflowState entity for a given session ID.

        Raises:
            EntityNotFoundError: If state file does not exist.
        """
        state_file = self._state_root / "workflow.json"
        if not state_file.exists():
            raise EntityNotFoundError(f"Workflow state for session '{session_id}' not found.")

        with state_file.open(encoding="utf-8") as f:
            data = json.load(f)

        started_at = parse_datetime(data.get("started_at"))
        updated_at = parse_datetime(data.get("updated_at"))

        return WorkflowState(
            session_id=data.get("session_id", session_id),
            active_phase=data.get("active_phase", "brainstorming"),
            checkpoint=int(data.get("checkpoint", 1)),
            status=_coerce_phase_status(data.get("status", "IN_PROGRESS")),
            started_at=started_at,
            updated_at=updated_at,
        )

    def save_state(self, state: WorkflowState, expected_revision: int | None = None) -> None:
        """Persists the WorkflowState entity atomically to workflow.json.

        Raises:
            RevisionConflictError: If a concurrent write conflict is detected.
        """
        state_file = self._state_root / "workflow.json"
        current_revision = 0
        if state_file.exists():
            try:
                with state_file.open(encoding="utf-8") as f:
                    existing = json.load(f)
                    current_revision = int(existing.get("revision", 0))
            except Exception:
                current_revision = 0

            if expected_revision is not None and current_revision != expected_revision:
                raise RevisionConflictError(
                    f"Revision conflict: expected {expected_revision}, current is {current_revision}."
                )

        new_revision = current_revision + 1
        payload = {
            "session_id": state.session_id,
            "active_phase": state.active_phase,
            "checkpoint": state.checkpoint,
            "status": state.status.value,
            "started_at": state.started_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
            "revision": new_revision,
        }
        atomic_write_json(_rel_path_str(state_file), payload)
        self._sync_session_aggregate(state)

    def record_checkpoint(self, checkpoint: Checkpoint) -> None:
        """Appends a new Checkpoint record to checkpoints.json."""
        checkpoints_file = self._state_root / "checkpoints.json"
        checkpoints: list[dict[str, Any]] = []
        if checkpoints_file.exists():
            with checkpoints_file.open(encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, list):
                    checkpoints = cast(list[dict[str, Any]], raw)

        checkpoints.append({
            "sequence": checkpoint.sequence,
            "phase": checkpoint.phase,
            "status": checkpoint.status.value,
            "validated_by": checkpoint.validated_by.value if checkpoint.validated_by else None,
            "recorded_at": checkpoint.recorded_at.isoformat(),
        })
        atomic_write_json(_rel_path_str(checkpoints_file), checkpoints)

    def list_checkpoints(self, session_id: str) -> list[Checkpoint]:
        """Lists all recorded Checkpoints for the session."""
        checkpoints_file = self._state_root / "checkpoints.json"
        if not checkpoints_file.exists():
            return []
        with checkpoints_file.open(encoding="utf-8") as f:
            data = json.load(f)
        return [
            Checkpoint(
                sequence=item["sequence"],
                phase=item["phase"],
                status=_coerce_phase_status(item.get("status", "IN_PROGRESS")),
                validated_by=RoleId(item["validated_by"]) if item.get("validated_by") else None,
                recorded_at=parse_datetime(item.get("recorded_at")),
            )
            for item in data
        ]

    def read_state(self, key: str | None = None) -> Any:
        """Reads full state or a specific key from workflow.json."""
        state_file = self._state_root / "workflow.json"
        if not state_file.exists():
            raise EntityNotFoundError(f"State file '{state_file}' does not exist.")
        with state_file.open(encoding="utf-8") as f:
            data = json.load(f)
        if key is not None:
            return data.get(key)
        return data

    def write_state(self, key: str, value: Any) -> None:
        """Mutates a single key in workflow.json atomically."""
        state_file = self._state_root / "workflow.json"
        data: dict[str, Any] = {}
        if state_file.exists():
            with state_file.open(encoding="utf-8") as f:
                raw_d = json.load(f)
                if isinstance(raw_d, dict):
                    data = cast(dict[str, Any], raw_d)
        data[key] = value
        atomic_write_json(_rel_path_str(state_file), data)

    def _sync_session_aggregate(self, state: WorkflowState) -> None:
        """Syncs active state back to top-level .session.json view."""
        session_file = self._state_root.parent / ".session.json"
        aggregate = {
            "session_id": state.session_id,
            "checkpoint": state.checkpoint,
            "status": state.status.value.lower(),
            "active_phase": state.active_phase,
            "updated_at": state.updated_at.isoformat(),
        }
        atomic_write_json(_rel_path_str(session_file), aggregate)


def parse_datetime(dt_str: str | None) -> datetime:
    if not dt_str:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return datetime.now(timezone.utc)
