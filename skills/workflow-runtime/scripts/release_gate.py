# release_gate.py
"""
Hard pre-release validation gate for AIWF.
Validates ALL conditions before allowing any release action to proceed.
Cannot be bypassed by any CLI argument.
"""
import os
import re
from datetime import datetime, timezone
from typing import Optional

from ledger import ImplementationLedger, LedgerNotFoundError  # type: ignore
from atomic_writer import write_json_atomic  # type: ignore


class PrematureReleaseError(PermissionError):
    """Raised when release is attempted before all gates pass."""
    pass


class PartialReleaseConfirmationError(ValueError):
    """Raised when the user's confirmation text doesn't match the required pattern."""
    pass


class ReleaseGate:
    """
    Hard release gate validator.
    All 8 conditions must pass before release is allowed.
    All failing conditions are collected and reported together.
    """

    # Required pattern for partial release confirmation
    PARTIAL_CONFIRM_PATTERN = r"^Approve partial release for (.+)$"

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root
        self._ledger = ImplementationLedger(workspace_root)

    def validate(self) -> tuple[bool, str]:
        """
        Run all release gate validation conditions.
        
        Returns:
            (True, "") if all conditions pass.
            (False, "<reason>") with all failing conditions if blocked.
        """
        failures = []

        # Condition 1: Ledger must exist
        if not self._ledger.exists():
            return False, (
                "Release blocked: implementation-ledger.json not found. "
                "Run /implement first."
            )

        ledger = self._ledger.load()

        # Condition 2: All phases must be completed
        phases = ledger.get("phases", [])
        incomplete_phases = [
            p.get("id", "") for p in phases
            if p.get("status") != "completed"
        ]
        if incomplete_phases:
            failures.append(
                f"Incomplete phases: {', '.join(incomplete_phases)}. "
                f"Continue with /implement."
            )

        # Condition 3: All tasks must be completed (no failed tasks)
        tasks = ledger.get("tasks", {})
        failed_tasks = [
            tid for tid, td in tasks.items()
            if td.get("status") == "failed"
        ]
        if failed_tasks:
            failures.append(
                f"Failed tasks: {', '.join(failed_tasks)}. "
                f"Fix issues and re-run /implement."
            )

        pending_tasks = [
            tid for tid, td in tasks.items()
            if td.get("status") in ("pending", "in_progress")
        ]
        if pending_tasks:
            failures.append(
                f"Pending/incomplete tasks: {', '.join(pending_tasks)}. "
                f"Complete implementation first."
            )

        # Condition 4: No active workers (check workers.json if available)
        workers_fail = self._check_workers()
        if workers_fail:
            failures.append(workers_fail)

        # Condition 5: No active file locks
        locks_fail = self._check_locks()
        if locks_fail:
            failures.append(locks_fail)

        # Condition 6: Debug report must exist and PASS
        debug_fail = self._check_debug_report(ledger)
        if debug_fail:
            failures.append(debug_fail)

        # Condition 7: Verify report must exist and PASS
        verify_fail = self._check_verify_report(ledger)
        if verify_fail:
            failures.append(verify_fail)

        # Condition 8: implementation_status must be "completed"
        impl_status = ledger.get("implementation_status", "not_started")
        if impl_status != "completed":
            failures.append(
                f"Implementation status is '{impl_status}', not 'completed'. "
                f"All phases must complete before release."
            )

        if failures:
            reason = (
                f"Release blocked for {ledger.get('feature_id', 'UNKNOWN')}:\n"
                + "\n".join(f"  • {f}" for f in failures)
            )
            return False, reason

        return True, ""

    def validate_partial(self, phase_id: str) -> tuple[bool, str]:
        """
        Validate a partial release for a single phase.
        Less strict than full release: only checks phase completeness.
        """
        failures = []

        if not self._ledger.exists():
            return False, "Ledger not found. Run /implement first."

        ledger = self._ledger.load()
        phases = ledger.get("phases", [])

        # Find the specified phase
        target_phase = None
        for p in phases:
            if p.get("id") == phase_id:
                target_phase = p
                break

        if target_phase is None:
            return False, f"Phase '{phase_id}' not found in ledger."

        if target_phase.get("status") != "completed":
            failures.append(f"Phase '{phase_id}' is not completed yet.")

        # Check no active workers/locks for this phase
        workers_fail = self._check_workers()
        if workers_fail:
            failures.append(workers_fail)

        if failures:
            return False, "\n".join(f"  • {f}" for f in failures)

        return True, ""

    def require_explicit_confirmation(self, text: str, phase_id: Optional[str] = None) -> bool:
        """
        Validate that user input exactly matches the required confirmation pattern.
        
        For partial release: "Approve partial release for Phase X"
        
        Args:
            text: The user's confirmation text.
            phase_id: The phase ID to validate against (for partial release).
        
        Returns:
            True if confirmation matches exactly.
        
        Raises:
            PartialReleaseConfirmationError: If text doesn't match.
        """
        text = text.strip()
        match = re.match(self.PARTIAL_CONFIRM_PATTERN, text)
        
        if not match:
            expected_phase = phase_id if phase_id else "Phase X"
            raise PartialReleaseConfirmationError(
                f"Confirmation text does not match required pattern.\n"
                f"Required: 'Approve partial release for {expected_phase}'\n"
                f"Got: '{text}'"
            )

        if phase_id and match.group(1).strip() != phase_id:
            raise PartialReleaseConfirmationError(
                f"Confirmation is for '{match.group(1)}' but expected '{phase_id}'."
            )

        return True

    def create_partial_release_note(
        self,
        phase_id: str,
        workspace_root: Optional[str] = None,
    ) -> str:
        """
        Create a partial release note file.
        Feature is NOT marked as fully released.
        Returns path to the created note.
        """
        ledger = self._ledger.load()
        feature_id = ledger.get("feature_id", "UNKNOWN")
        safe_phase = phase_id.replace(" ", "_").replace("/", "_")

        releases_dir = os.path.join(
            workspace_root or ".",
            "docs", "releases"
        )
        os.makedirs(releases_dir, exist_ok=True)

        note_path = os.path.join(
            releases_dir,
            f"{feature_id}_{safe_phase}_partial_release.md",
        )

        now = datetime.now(timezone.utc).isoformat()
        note = (
            f"# Partial Release Note: {feature_id} — {phase_id}\n\n"
            f"**Date**: {now}\n"
            f"**Feature**: {feature_id} — {ledger.get('feature_name', '')}\n"
            f"**Phase Released**: {phase_id}\n"
            f"**Partial**: true\n"
            f"**Full Feature Released**: false\n\n"
            f"## ⚠️ Warning\n\n"
            f"This is a **PARTIAL** release. The full feature implementation "
            f"continues in remaining phases.\n\n"
            f"## Released Tasks\n\n"
        )

        # List tasks in this phase
        phase_tasks = []
        for p in ledger.get("phases", []):
            if p.get("id") == phase_id:
                phase_tasks = p.get("tasks", [])
                break

        for task_id in phase_tasks:
            note += f"- {task_id}\n"

        with open(note_path, "w", encoding="utf-8") as f:
            f.write(note)

        return note_path

    # ------------------------------------------------------------------
    # Internal validation helpers
    # ------------------------------------------------------------------

    def _check_workers(self) -> Optional[str]:
        """Check workers.json for active workers. Returns failure message or None."""
        workers_path = os.path.join(
            self._workspace_root or ".",
            ".agents", "runtime", "workers.json"
        )
        if not os.path.exists(workers_path):
            return None  # No workers file = no active workers

        from atomic_writer import read_json_safe  # type: ignore
        data = read_json_safe(workers_path) or {}
        workers = data.get("workers", {})
        active = [
            wid for wid, wd in workers.items()
            if wd.get("status") in ("running", "starting")
        ]
        if active:
            return (
                f"{len(active)} active worker(s) still running. "
                f"Run 'implement abort' to terminate."
            )
        return None

    def _check_locks(self) -> Optional[str]:
        """Check file-locks.json for active locks. Returns failure message or None."""
        locks_path = os.path.join(
            self._workspace_root or ".",
            ".agents", "runtime", "file-locks.json"
        )
        if not os.path.exists(locks_path):
            return None

        from atomic_writer import read_json_safe  # type: ignore
        data = read_json_safe(locks_path) or {}
        locks = data.get("locks", {})
        active = [f for f, ld in locks.items() if ld.get("status") == "active"]
        if active:
            return (
                f"{len(active)} active file lock(s) remain. "
                f"Run 'state doctor' to inspect and clear."
            )
        return None

    def _check_debug_report(self, ledger: dict) -> Optional[str]:
        """Check that debug report exists and has status PASS."""
        feature_id = ledger.get("feature_id", "")
        debug_path = os.path.join(
            self._workspace_root or ".",
            "docs", "debug", f"{feature_id}_debug.md"
        )
        if not os.path.exists(debug_path):
            return (
                f"Debug report not found at docs/debug/{feature_id}_debug.md. "
                f"Run /debug first."
            )

        # Check for PASS marker in debug report
        try:
            with open(debug_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "PASS" not in content and "pass" not in content.lower():
                return (
                    f"Debug report exists but does not contain 'PASS'. "
                    f"Fix issues and re-run /debug."
                )
        except OSError:
            return f"Cannot read debug report at {debug_path}."

        return None

    def _check_verify_report(self, ledger: dict) -> Optional[str]:
        """Check that verify report exists and has status PASS."""
        feature_id = ledger.get("feature_id", "")
        verify_path = os.path.join(
            self._workspace_root or ".",
            "docs", "reviews", f"{feature_id}_verify.md"
        )
        if not os.path.exists(verify_path):
            return (
                f"Verify report not found at docs/reviews/{feature_id}_verify.md. "
                f"Run /verify first."
            )

        try:
            with open(verify_path, "r", encoding="utf-8") as f:
                content = f.read()
            if "PASS" not in content and "pass" not in content.lower():
                return (
                    f"Verify report exists but does not contain 'PASS'. "
                    f"Fix issues and re-run /verify."
                )
        except OSError:
            return f"Cannot read verify report at {verify_path}."

        return None
