# ledger.py
"""
Implementation Ledger — tracks progress of blueprint execution phases and tasks.
Single source of truth for what has been implemented and what remains.
Backward-compatible: single-phase blueprints get a synthetic "Phase 1".
"""
import os
from datetime import datetime, timezone
from typing import Optional

from atomic_writer import write_json_atomic, read_json_safe  # type: ignore

LEDGER_PATH = os.path.join(".agents", "runtime", "implementation-ledger.json")

# Phase status lifecycle (monotonic — no reversals)
PHASE_STATUS_PENDING = "pending"
PHASE_STATUS_IN_PROGRESS = "in_progress"
PHASE_STATUS_COMPLETED = "completed"

TASK_STATUS_PENDING = "pending"
TASK_STATUS_IN_PROGRESS = "in_progress"
TASK_STATUS_COMPLETED = "completed"
TASK_STATUS_FAILED = "failed"

# Feature implementation status
IMPL_STATUS_NOT_STARTED = "not_started"
IMPL_STATUS_IN_PROGRESS = "in_progress"
IMPL_STATUS_COMPLETED = "completed"


class LedgerNotFoundError(FileNotFoundError):
    """Raised when the implementation ledger is missing when required."""
    pass


class InvalidPhaseTransitionError(ValueError):
    """Raised when a non-monotonic phase status change is attempted."""
    pass


class ImplementationLedger:
    """
    CRUD manager for implementation-ledger.json.
    All writes are atomic via AtomicWriter.
    Missing ledger returns empty template (not None) on load().
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root
        if workspace_root:
            self._path = os.path.join(workspace_root, LEDGER_PATH)
        else:
            self._path = LEDGER_PATH

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def load(self) -> dict:
        """
        Load the ledger from disk.
        Returns an empty template dict if file is missing.
        Never returns None.
        """
        data = read_json_safe(self._path)
        if data is None or not isinstance(data, dict):
            return self._empty_template()
        return data

    def save(self, data: dict) -> None:
        """Write ledger to disk atomically."""
        parent = os.path.dirname(self._path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        write_json_atomic(self._path, data)

    def exists(self) -> bool:
        """True if ledger file exists on disk."""
        return os.path.exists(self._path)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    def init_from_blueprint(self, blueprint_json: dict) -> dict:
        """
        Parse a blueprint JSON dict and create a fresh ledger.
        All phases and tasks initialized to 'pending'.
        
        Backward compat: If blueprint has no 'phases' key, all tasks
        from 'implementation_packages' or 'tasks' are wrapped in synthetic Phase 1.
        
        Args:
            blueprint_json: Loaded JSON from docs/blueprints/FEAT-XXX_blueprint.json
                (or docs/blueprints/<feature-slug>/phase-NN-<phase-slug>/phase-blueprint.json)
        
        Returns:
            Ledger dict (also saved to disk).
        
        Raises:
            ValueError: If feature_id is missing from blueprint.
        """
        feature_id = blueprint_json.get("feature_id") or blueprint_json.get("feature_id")
        if not feature_id:
            raise ValueError("Blueprint must have 'feature_id' field.")

        # Extract phases from blueprint
        bp_phases = blueprint_json.get("phases", [])
        impl_packages = blueprint_json.get("implementation_packages", [])
        
        if bp_phases:
            # Modern multi-phase blueprint
            phases = self._parse_phases(bp_phases, impl_packages)
        else:
            # Auto-detect phases from 'module' field of impl packages
            # e.g. module "Phase 1" → separate phase for each distinct module value
            from collections import OrderedDict
            phase_map: OrderedDict = OrderedDict()
            for pkg in impl_packages:
                module = pkg.get("module", "Phase 1")
                if module not in phase_map:
                    phase_map[module] = []
                task_id = pkg.get("task_id", "")
                if task_id:
                    phase_map[module].append(task_id)

            if len(phase_map) > 1:
                # Multi-phase detected via module field
                phases = [
                    {
                        "id": module_name,
                        "title": module_name,
                        "status": PHASE_STATUS_PENDING,
                        "completion_type": "phase_complete",
                        "tasks": task_ids,
                        "started_at": None,
                        "completed_at": None,
                    }
                    for module_name, task_ids in phase_map.items()
                ]
            else:
                # Single phase or no module field
                all_task_ids = [p.get("task_id", f"Task {i+1}") for i, p in enumerate(impl_packages)]
                phases = [
                    {
                        "id": "Phase 1",
                        "title": "Implementation Phase",
                        "status": PHASE_STATUS_PENDING,
                        "completion_type": "feature_complete",
                        "tasks": all_task_ids,
                        "started_at": None,
                        "completed_at": None,
                    }
                ]

        # Build tasks dict
        tasks = {}
        for pkg in impl_packages:
            task_id = pkg.get("task_id", "")
            if task_id:
                # Find which phase this task belongs to
                phase_id = self._find_phase_for_task(task_id, phases)
                tasks[task_id] = {
                    "status": TASK_STATUS_PENDING,
                    "phase": phase_id,
                    "started_at": None,
                    "completed_at": None,
                    "error": None,
                }

        now = datetime.now(timezone.utc).isoformat()
        ledger = {
            "feature_id": feature_id,
            "feature_name": blueprint_json.get("feature_name", ""),
            "blueprint_path": blueprint_json.get("_blueprint_path", ""),
            "implementation_status": IMPL_STATUS_NOT_STARTED,
            "current_phase": phases[0]["id"] if phases else None,
            "phases": phases,
            "tasks": tasks,
            "release_allowed": False,
            "release_block_reason": "Implementation not started.",
            "debug_allowed": False,
            "verify_allowed": False,
            "orphan_process_check": "pass",
            "created_at": now,
            "updated_at": now,
        }
        self.save(ledger)
        return ledger

    # ------------------------------------------------------------------
    # Phase lifecycle
    # ------------------------------------------------------------------

    def mark_phase_started(self, phase_id: str) -> None:
        """Mark a phase as in_progress (monotonic: cannot revert completed phase)."""
        ledger = self.load()
        phase = self._get_phase(ledger, phase_id)
        if phase["status"] == PHASE_STATUS_COMPLETED:
            return  # Idempotent: already done, don't revert
        if phase["status"] != PHASE_STATUS_IN_PROGRESS:
            phase["status"] = PHASE_STATUS_IN_PROGRESS
            phase["started_at"] = datetime.now(timezone.utc).isoformat()
        ledger["current_phase"] = phase_id
        ledger["implementation_status"] = IMPL_STATUS_IN_PROGRESS
        ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(ledger)

    def mark_phase_completed(self, phase_id: str) -> None:
        """
        Mark a phase as completed and recompute implementation_status.
        Raises InvalidPhaseTransitionError if attempting to un-complete.
        """
        ledger = self.load()
        phase = self._get_phase(ledger, phase_id)
        
        if phase["status"] == PHASE_STATUS_COMPLETED:
            return  # Idempotent

        phase["status"] = PHASE_STATUS_COMPLETED
        phase["completed_at"] = datetime.now(timezone.utc).isoformat()

        # Recompute implementation_status
        all_complete = all(
            p.get("status") == PHASE_STATUS_COMPLETED
            for p in ledger.get("phases", [])
        )
        ledger["implementation_status"] = (
            IMPL_STATUS_COMPLETED if all_complete else IMPL_STATUS_IN_PROGRESS
        )
        if all_complete:
            ledger["debug_allowed"] = True
        ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(ledger)

    # ------------------------------------------------------------------
    # Task lifecycle
    # ------------------------------------------------------------------

    def mark_task_completed(self, task_id: str) -> None:
        """Mark a single task as completed inside its parent phase."""
        ledger = self.load()
        tasks = ledger.get("tasks", {})
        if task_id in tasks:
            tasks[task_id]["status"] = TASK_STATUS_COMPLETED
            tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            tasks[task_id]["error"] = None
        ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(ledger)

    def mark_task_failed(self, task_id: str, error: str = "") -> None:
        """Mark a task as failed with an error message."""
        ledger = self.load()
        tasks = ledger.get("tasks", {})
        if task_id in tasks:
            tasks[task_id]["status"] = TASK_STATUS_FAILED
            tasks[task_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
            tasks[task_id]["error"] = error
        ledger["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.save(ledger)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_next_incomplete_phase(self) -> Optional[str]:
        """Return the first phase with status != 'completed', or None if all done."""
        ledger = self.load()
        for phase in ledger.get("phases", []):
            if phase.get("status") != PHASE_STATUS_COMPLETED:
                return phase.get("id")
        return None

    def is_feature_complete(self) -> bool:
        """True if all phases are completed."""
        ledger = self.load()
        phases = ledger.get("phases", [])
        if not phases:
            return False
        return all(p.get("status") == PHASE_STATUS_COMPLETED for p in phases)

    def get_release_gate_status(self) -> dict:
        """Return the current gate flags from ledger."""
        ledger = self.load()
        return {
            "release_allowed": ledger.get("release_allowed", False),
            "release_block_reason": ledger.get("release_block_reason", ""),
            "debug_allowed": ledger.get("debug_allowed", False),
            "verify_allowed": ledger.get("verify_allowed", False),
            "implementation_status": ledger.get("implementation_status", IMPL_STATUS_NOT_STARTED),
        }

    def get_phase_summary(self) -> list[dict]:
        """Return list of {phase_id, title, status, tasks} for display."""
        ledger = self.load()
        summary = []
        for phase in ledger.get("phases", []):
            summary.append({
                "phase_id": phase.get("id", ""),
                "title": phase.get("title", ""),
                "status": phase.get("status", PHASE_STATUS_PENDING),
                "tasks": phase.get("tasks", []),
                "started_at": phase.get("started_at"),
                "completed_at": phase.get("completed_at"),
            })
        return summary

    def get_failed_tasks(self) -> list[str]:
        """Return list of task_ids with status == 'failed'."""
        ledger = self.load()
        return [
            tid for tid, td in ledger.get("tasks", {}).items()
            if td.get("status") == TASK_STATUS_FAILED
        ]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _empty_template(self) -> dict:
        return {
            "feature_id": "",
            "feature_name": "",
            "blueprint_path": "",
            "implementation_status": IMPL_STATUS_NOT_STARTED,
            "current_phase": None,
            "phases": [],
            "tasks": {},
            "release_allowed": False,
            "release_block_reason": "Implementation ledger not initialized.",
            "debug_allowed": False,
            "verify_allowed": False,
            "orphan_process_check": "pass",
            "created_at": None,
            "updated_at": None,
        }

    def _parse_phases(
        self,
        bp_phases: list,
        impl_packages: list,
    ) -> list:
        """Parse blueprint phases list into ledger phase records."""
        phases = []
        for bp_phase in bp_phases:
            # Get task IDs for this phase from impl_packages
            phase_name = bp_phase.get("phase_name", bp_phase.get("id", ""))
            task_ids = bp_phase.get("tasks", [])
            if not task_ids:
                # Auto-assign tasks from implementation_packages that mention this phase
                task_ids = [
                    p.get("task_id", "")
                    for p in impl_packages
                    if self._task_in_phase(p, phase_name)
                ]
            phases.append({
                "id": phase_name,
                "title": bp_phase.get("title", phase_name),
                "status": PHASE_STATUS_PENDING,
                "completion_type": bp_phase.get("completion_type", "phase_complete"),
                "tasks": task_ids,
                "started_at": None,
                "completed_at": None,
            })
        return phases

    def _task_in_phase(self, pkg: dict, phase_name: str) -> bool:
        """Check if an impl_package belongs to a phase by name match."""
        module = pkg.get("module", "")
        task_id = pkg.get("task_id", "")
        return phase_name.lower() in module.lower() or phase_name.lower() in task_id.lower()

    def _get_phase(self, ledger: dict, phase_id: str) -> dict:
        """Find a phase in ledger by ID. Raises ValueError if not found."""
        for phase in ledger.get("phases", []):
            if phase.get("id") == phase_id:
                return phase
        raise ValueError(f"Phase '{phase_id}' not found in ledger.")

    def _find_phase_for_task(self, task_id: str, phases: list) -> str:
        """Find the phase ID that contains a given task_id."""
        for phase in phases:
            if task_id in phase.get("tasks", []):
                return phase.get("id", "Phase 1")
        return "Phase 1"
