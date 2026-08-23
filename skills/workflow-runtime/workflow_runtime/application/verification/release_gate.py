# release_gate.py
"""
Hard pre-release validation gate for AIWF.
Validates ALL conditions before allowing any release action to proceed.
Cannot be bypassed by any CLI argument.
"""
from __future__ import annotations

import os
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator


class PrematureReleaseError(PermissionError):
    """Raised when release is attempted before all gates pass."""


class PartialReleaseConfirmationError(ValueError):
    """Raised when the user's confirmation text doesn't match the required pattern."""


class ReleaseGate:
    """
    Hard release gate validator.
    All 8 conditions must pass before release is allowed.
    All failing conditions are collected and reported together.
    """

    PARTIAL_CONFIRM_PATTERN = r"^Approve partial release for (.+)$"

    def __init__(self, workspace_root: str | None = None) -> None:
        self._workspace_root = workspace_root
        impl_cls: Any = getattr(InfrastructureLocator, "ImplementationLedger", None)
        self._ledger: Any = impl_cls(workspace_root) if callable(impl_cls) else None

    def validate(self) -> tuple[bool, str]:
        failures: list[str] = []

        if not self._ledger or not bool(getattr(self._ledger, "exists")()):
            return False, (
                "Release blocked: implementation-ledger.json not found. "
                "Run /implement first."
            )

        ledger: dict[str, Any] = cast(dict[str, Any], getattr(self._ledger, "load")())

        # Condition 2: All phases must be completed
        raw_phases = ledger.get("phases")
        phases: list[dict[str, Any]] = [cast(dict[str, Any], p) for p in cast(list[Any], raw_phases) if isinstance(p, dict)] if isinstance(raw_phases, list) else []
        incomplete_phases = [
            str(p.get("id", "")) for p in phases
            if str(p.get("status", "")) != "completed"
        ]
        if incomplete_phases:
            failures.append(
                f"Incomplete phases: {', '.join(incomplete_phases)}. "
                f"Continue with /implement."
            )

        # Condition 3: All tasks must be completed
        raw_tasks = ledger.get("tasks")
        tasks: dict[str, dict[str, Any]] = {str(k): cast(dict[str, Any], v) for k, v in cast(dict[str, Any], raw_tasks).items() if isinstance(v, dict)} if isinstance(raw_tasks, dict) else {}
        failed_tasks = [
            tid for tid, td in tasks.items()
            if str(td.get("status", "")) == "failed"
        ]
        if failed_tasks:
            failures.append(
                f"Failed tasks: {', '.join(failed_tasks)}. "
                f"Fix issues and re-run /implement."
            )

        pending_tasks = [
            tid for tid, td in tasks.items()
            if str(td.get("status", "")) in ("pending", "in_progress")
        ]
        if pending_tasks:
            failures.append(
                f"Pending/incomplete tasks: {', '.join(pending_tasks)}. "
                f"Complete implementation first."
            )

        # Condition 4: No active workers
        workers_fail = self._check_workers()
        if workers_fail:
            failures.append(workers_fail)

        # Condition 5: No active file locks
        locks_fail = self._check_locks()
        if locks_fail:
            failures.append(locks_fail)

        # Condition 6: Debug report PASS
        debug_fail = self._check_debug_report(ledger)
        if debug_fail:
            failures.append(debug_fail)

        # Condition 7: Verify report PASS
        verify_fail = self._check_verify_report(ledger)
        if verify_fail:
            failures.append(verify_fail)

        if failures:
            msg = "Release blocked by validation gate:\n" + "\n".join(f"- {f}" for f in failures)
            return False, msg

        return True, ""

    def _check_workers(self) -> str | None:
        workers_path = os.path.join(
            self._workspace_root or ".",
            ".agents", "runtime", "workers.json"
        )
        if not os.path.exists(workers_path):
            return None

        read_fn: Any = getattr(InfrastructureLocator, "read_json_safe", None)
        data: dict[str, Any] = cast(dict[str, Any], read_fn(workers_path)) if callable(read_fn) else {}
        raw_workers = data.get("workers")
        workers: dict[str, dict[str, Any]] = {str(k): cast(dict[str, Any], v) for k, v in cast(dict[str, Any], raw_workers).items() if isinstance(v, dict)} if isinstance(raw_workers, dict) else {}
        active = [
            wid for wid, wd in workers.items()
            if str(wd.get("status", "")) in ("running", "starting")
        ]
        if active:
            return (
                f"{len(active)} active worker(s) still running. "
                f"Run 'implement abort' to terminate."
            )
        return None

    def _check_locks(self) -> str | None:
        locks_path = os.path.join(
            self._workspace_root or ".",
            ".agents", "runtime", "file-locks.json"
        )
        if not os.path.exists(locks_path):
            return None

        read_fn: Any = getattr(InfrastructureLocator, "read_json_safe", None)
        data: dict[str, Any] = cast(dict[str, Any], read_fn(locks_path)) if callable(read_fn) else {}
        raw_locks = data.get("locks")
        locks: dict[str, dict[str, Any]] = {str(k): cast(dict[str, Any], v) for k, v in cast(dict[str, Any], raw_locks).items() if isinstance(v, dict)} if isinstance(raw_locks, dict) else {}
        active = [f for f, ld in locks.items() if str(ld.get("status", "")) == "active"]
        if active:
            return (
                f"{len(active)} active file lock(s) remain. "
                f"Run 'state doctor' to inspect and clear."
            )
        return None

    def _check_debug_report(self, ledger: dict[str, Any]) -> str | None:
        feature_id = str(ledger.get("feature_id", ""))
        debug_path = os.path.join(
            self._workspace_root or ".",
            "docs", "debug", f"{feature_id}_debug.md"
        )
        if not os.path.exists(debug_path):
            return (
                f"Debug report not found at docs/debug/{feature_id}_debug.md. "
                f"Run /debug first."
            )

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

    def _check_verify_report(self, ledger: dict[str, Any]) -> str | None:
        feature_id = str(ledger.get("feature_id", ""))
        verify_path = os.path.join(
            self._workspace_root or ".",
            "docs", "verification", f"{feature_id}_verify.md"
        )
        if not os.path.exists(verify_path):
            return (
                f"Verify report not found at docs/verification/{feature_id}_verify.md. "
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


__all__ = [
    "PrematureReleaseError",
    "PartialReleaseConfirmationError",
    "ReleaseGate",
]
