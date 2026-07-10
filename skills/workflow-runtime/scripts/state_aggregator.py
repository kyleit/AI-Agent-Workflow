# state_aggregator.py
"""
State Aggregator for AIWF runtime.
Reads all canonical split-state sub-directories and computes derived fields
(suggested_next_skill, release_allowed, debug_allowed, etc.).
Writes the aggregated result to dashboard.json.
Optionally writes a backward-compatible deprecated .session.json snapshot.
"""
import os
from datetime import datetime, timezone
from typing import Optional

from atomic_writer import write_json_atomic, read_json_safe  # type: ignore
from state_path import (  # type: ignore
    get_state_root, get_subdir, get_state_file,
    get_dashboard_path, get_legacy_session_path, ensure_dirs,
)


# ---------------------------------------------------------------------------
# Aggregation Logic Constants
# ---------------------------------------------------------------------------

# Phase-based implementation status to suggested skill mapping
_IMPL_SKILL_MAP = {
    "not_started":   "initialize-workflow",
    "in_progress":   "blueprint-to-implementation",
    "completed":     "implementation-to-debug",
}


class StateAggregator:
    """
    Reads all canonical sub-state JSON files and produces:
    - dashboard.json: The unified, computed view (always up to date).
    - .session.json: Optional deprecated backward-compat snapshot.

    Never crashes: degraded mode returns _health='degraded' on parse errors.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root

    def aggregate(self) -> dict:
        """
        Read all sub-state JSON files and compute derived fields.
        
        Returns:
            Dashboard dict with keys:
              current_skill, current_command, checkpoint,
              suggested_next_skill, release_allowed, debug_allowed,
              verify_allowed, release_block_reason, implementation_status,
              phase_status[], worker_count, lock_count,
              _generated_at, _source, _health
        """
        health = "healthy"
        errors = []

        # Read each sub-state file
        workflow = self._read_substate("workflow", errors)
        runtime = self._read_substate("runtime", errors)
        context = self._read_substate("context", errors)
        project = self._read_substate("project", errors)
        recovery = self._read_substate("recovery", errors)

        if errors:
            health = "degraded"

        # Phase status
        phases = runtime.get("phases", {})
        phase_status = []
        all_phases_complete = True
        any_phase_in_progress = False

        for phase_id, phase_data in phases.items():
            status = phase_data.get("status", "pending")
            phase_status.append({
                "phase_id": phase_id,
                "status": status,
                "started_at": phase_data.get("started_at"),
                "completed_at": phase_data.get("completed_at"),
            })
            if status != "completed":
                all_phases_complete = False
            if status == "in_progress":
                any_phase_in_progress = True

        # Task counts
        tasks = runtime.get("tasks", {})
        failed_tasks = [t for t, d in tasks.items() if d.get("status") == "failed"]
        pending_tasks = [t for t, d in tasks.items() if d.get("status") == "pending"]

        # Worker and lock counts
        active_workers = runtime.get("active_workers", {})
        worker_count = sum(
            1 for w in active_workers.values()
            if w.get("status") in ("running", "starting")
        )
        active_locks = runtime.get("active_locks", {})
        lock_count = len(active_locks)

        # Quality gate statuses from workflow
        debug_status = workflow.get("debug_status", "not_started")
        verify_status = workflow.get("verify_status", "not_started")
        release_status = workflow.get("release_status", "not_started")

        # Compute derived gate flags
        debug_allowed, verify_allowed, release_allowed, release_block_reason = \
            self._compute_gates(
                phases=phases,
                all_phases_complete=all_phases_complete,
                any_phase_in_progress=any_phase_in_progress,
                failed_tasks=failed_tasks,
                worker_count=worker_count,
                lock_count=lock_count,
                debug_status=debug_status,
                verify_status=verify_status,
            )

        # Compute suggested_next_skill
        suggested_next_skill = self._compute_next_skill(
            workflow=workflow,
            all_phases_complete=all_phases_complete,
            any_phase_in_progress=any_phase_in_progress,
            debug_status=debug_status,
            verify_status=verify_status,
            release_status=release_status,
            failed_tasks=failed_tasks,
        )

        dashboard = {
            # Current position
            "current_skill": workflow.get("current_skill", ""),
            "current_command": workflow.get("current_command", ""),
            "current_step": workflow.get("current_step", ""),
            "checkpoint": workflow.get("checkpoint", 0),
            "feature_id": project.get("feature_id", workflow.get("feature_id", "")),

            # Computed recommendations
            "suggested_next_skill": suggested_next_skill,
            "release_allowed": release_allowed,
            "release_block_reason": release_block_reason,
            "debug_allowed": debug_allowed,
            "verify_allowed": verify_allowed,

            # Implementation state
            "implementation_status": workflow.get("implementation_status", "not_started"),
            "phase_status": phase_status,
            "failed_tasks": failed_tasks,
            "worker_count": worker_count,
            "lock_count": lock_count,

            # Quality gate state
            "debug_status": debug_status,
            "verify_status": verify_status,
            "release_status": release_status,

            # Context data passthrough
            "context": context,

            # Metadata
            "_generated_at": datetime.now(timezone.utc).isoformat(),
            "_source": "split_state",
            "_health": health,
            "_errors": errors,
        }

        return dashboard

    def write_dashboard(self) -> str:
        """
        Compute aggregated state and write to dashboard.json atomically.
        Returns the path to the written dashboard file.
        """
        ensure_dirs(self._workspace_root)
        dashboard = self.aggregate()
        path = get_dashboard_path(self._workspace_root)
        write_json_atomic(path, dashboard)
        return path

    def write_legacy_snapshot(self, dashboard: Optional[dict] = None) -> str:
        """
        Write a backward-compatible .session.json snapshot for legacy consumers
        (e.g., older Visualizer versions).
        
        Adds _deprecated: true and _source: dashboard.json markers.
        DOES NOT remove any existing fields — only adds new ones.
        Returns the path to the written snapshot file.
        """
        if dashboard is None:
            dashboard = self.aggregate()

        # Load existing .session.json to merge (don't lose legacy fields)
        legacy_path = get_legacy_session_path(self._workspace_root)
        existing = read_json_safe(legacy_path) or {}

        # Build snapshot preserving all legacy keys, overriding with fresh data
        snapshot = dict(existing)
        snapshot.update({
            # Fresh data from dashboard
            "current_skill": dashboard.get("current_skill", ""),
            "suggested_next_skill": dashboard.get("suggested_next_skill", ""),
            "checkpoint": dashboard.get("checkpoint", 0),
            "release_allowed": dashboard.get("release_allowed", False),
            "debug_allowed": dashboard.get("debug_allowed", False),
            "verify_allowed": dashboard.get("verify_allowed", False),
            "implementation_status": dashboard.get("implementation_status", ""),

            # Deprecation markers
            "_deprecated": True,
            "_generated": True,
            "_source": "dashboard.json",
            "_generated_at": dashboard.get("_generated_at", ""),
            "_health": dashboard.get("_health", "healthy"),
        })

        write_json_atomic(legacy_path, snapshot)
        return legacy_path

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _read_substate(self, category: str, errors: list) -> dict:
        """Read a sub-state file, gracefully handling missing/corrupt files.
        
        - File missing: returns {} silently (normal for fresh install)
        - File corrupt/invalid JSON: returns {} but adds to errors list → degraded health
        """
        try:
            path = get_state_file(category, self._workspace_root)
        except Exception as e:
            errors.append(f"Cannot resolve {category} state path: {e}")
            return {}

        if not os.path.exists(path):
            return {}  # Missing file is normal, not an error

        try:
            with open(path, "r", encoding="utf-8") as f:
                import json as _json
                data = _json.load(f)
            if not isinstance(data, dict):
                errors.append(f"State file {category} is not a JSON object.")
                return {}
            return data
        except Exception as e:
            errors.append(f"Cannot read/parse {category} state ({path}): {e}")
            return {}

    def _compute_gates(
        self,
        phases: dict,
        all_phases_complete: bool,
        any_phase_in_progress: bool,
        failed_tasks: list,
        worker_count: int,
        lock_count: int,
        debug_status: str,
        verify_status: str,
    ) -> tuple:
        """
        Compute debug_allowed, verify_allowed, release_allowed, release_block_reason.
        Gate rules (ordered, must all pass for release):
          1. All phases completed.
          2. No failed tasks.
          3. No active workers.
          4. No active locks.
          5. Debug PASS.
          6. Verify PASS.
        """
        block_reasons = []

        if phases and not all_phases_complete:
            incomplete = [
                pid for pid, pd in phases.items()
                if pd.get("status") != "completed"
            ]
            block_reasons.append(
                f"Incomplete phases: {', '.join(incomplete)}. Run /implement to continue."
            )

        if failed_tasks:
            block_reasons.append(
                f"Failed tasks: {', '.join(failed_tasks)}. Run /debug."
            )

        if worker_count > 0:
            block_reasons.append(
                f"{worker_count} active worker(s) still running. Wait or run 'implement abort'."
            )

        if lock_count > 0:
            block_reasons.append(
                f"{lock_count} active file lock(s). Run 'state doctor' to inspect."
            )

        debug_allowed = bool(
            all_phases_complete
            and not failed_tasks
            and worker_count == 0
        )

        if debug_status != "pass":
            if debug_allowed:
                block_reasons.append("Debug report not PASS. Run /debug.")
            verify_allowed = False
        else:
            verify_allowed = True

        if verify_status != "pass":
            if verify_allowed:
                block_reasons.append("Verify report not PASS. Run /verify.")
            release_allowed = False
        else:
            release_allowed = len(block_reasons) == 0

        release_block_reason = "; ".join(block_reasons) if block_reasons else ""

        return debug_allowed, verify_allowed, release_allowed, release_block_reason

    def _compute_next_skill(
        self,
        workflow: dict,
        all_phases_complete: bool,
        any_phase_in_progress: bool,
        debug_status: str,
        verify_status: str,
        release_status: str,
        failed_tasks: list,
    ) -> str:
        """
        Determine the recommended next skill based on current state.
        """
        # If still implementing
        if any_phase_in_progress:
            return "blueprint-to-implementation"

        # If phases exist but not all complete
        if not all_phases_complete:
            return "blueprint-to-implementation"

        # If there are failed tasks
        if failed_tasks:
            return "implementation-to-debug"

        # All phases complete, check quality gates
        if debug_status != "pass":
            return "implementation-to-debug"

        if verify_status != "pass":
            return "debug-to-verify"

        if release_status not in ("completed",):
            return "implementation-to-release"

        return "done"


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------

def aggregate_and_write_dashboard(workspace_root: Optional[str] = None) -> str:
    """Convenience: aggregate state and write dashboard.json. Returns path."""
    return StateAggregator(workspace_root).write_dashboard()


def load_dashboard(workspace_root: Optional[str] = None) -> dict:
    """Load the current dashboard.json. Recomputes if file missing."""
    path = get_dashboard_path(workspace_root)
    if os.path.exists(path):
        data = read_json_safe(path)
        if isinstance(data, dict):
            return data
    # Dashboard missing → compute fresh
    return StateAggregator(workspace_root).aggregate()
