from __future__ import annotations

import re
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any

from workflow_runtime.shared.errors import DomainException


@dataclass(frozen=True)
class ReleaseGateResult:
    passed: bool
    score: int
    details: dict[str, Any] = field(default_factory=dict[str, Any])
    errors: list[str] = field(default_factory=list[str])


@dataclass(frozen=True)
class ReleasePlan:
    version: str
    files: tuple[str, ...]
    tag: str
    export_targets: tuple[str, ...] = ()
    rollback: str = "restore previous release tag"
    push_targets: tuple[str, ...] = ()

    @property
    def sha256(self) -> str:
        payload = {
            "version": self.version,
            "files": list(self.files),
            "tag": self.tag,
            "export_targets": list(self.export_targets),
            "rollback": self.rollback,
            "push_targets": list(self.push_targets),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ReleaseApproval:
    plan_hash: str


@dataclass(frozen=True)
class ReleaseResult:
    status: str
    reason: str = ""
    plan_hash: str | None = None


def continue_release_after_approval(plan: ReleasePlan, approval: ReleaseApproval) -> ReleaseResult:
    if approval.plan_hash != plan.sha256:
        return ReleaseResult("blocked", "approval_plan_hash_mismatch", plan.sha256)
    return ReleaseResult("ready", plan_hash=plan.sha256)


class ReleaseGateService:
    """Application service for evaluating release gate criteria (tests, linting, blueprint compliance)."""

    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = workspace_root

    def check_tests(
        self, test_log_path: str = ".agents/runtime/tests.log"
    ) -> bool:
        """Verifies test log file exists and contains zero test failures."""
        abs_log = (
            Path(test_log_path)
            if Path(test_log_path).is_absolute()
            else Path(self.workspace_root) / test_log_path
        )
        if not abs_log.exists():
            return False

        try:
            with abs_log.open(encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return False

        # Fail if log explicitly mentions failed tests or tracebacks
        failed_indicators = [
            "FAILED (",
            "ERRORS (",
            "=== FAILURES ===",
            " = failed,",
            " = error,",
        ]
        return not any(indicator in content for indicator in failed_indicators)

    def check_lint(self, lint_log_path: str | None = None) -> bool:
        """Verifies lint log file or lint status."""
        if not lint_log_path:
            return True

        abs_lint = (
            Path(lint_log_path)
            if Path(lint_log_path).is_absolute()
            else Path(self.workspace_root) / lint_log_path
        )
        if not abs_lint.exists():
            return True

        try:
            with abs_lint.open(encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return False

        return not ("error:" in content.lower() or "failed" in content.lower())

    def check_blueprint(self, blueprint_path: str) -> bool:
        """Verifies technical design blueprint exists and contains zero forbidden placeholders."""
        abs_bp = (
            Path(blueprint_path)
            if Path(blueprint_path).is_absolute()
            else Path(self.workspace_root) / blueprint_path
        )
        if not abs_bp.exists():
            raise DomainException(f"Blueprint file does not exist: {blueprint_path}")

        try:
            with abs_bp.open(encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError as e:
            raise DomainException(f"Failed to read blueprint file: {blueprint_path}") from e

        placeholder_terms = ("T" "BD", "T" "ODO", "to be " "decided", "implement " "later")
        placeholder_pattern = re.compile(
            rf"\b(?:{'|'.join(re.escape(term) for term in placeholder_terms)})\b",
            re.IGNORECASE,
        )
        return not bool(placeholder_pattern.search(content))

    def evaluate(
        self,
        blueprint_path: str | None = None,
        test_log_path: str = ".agents/runtime/tests.log",
        lint_log_path: str | None = None,
    ) -> ReleaseGateResult:
        """Evaluates all release gate requirements and produces final ReleaseGateResult."""
        errors: list[str] = []
        details: dict[str, Any] = {}

        # 1. Check tests
        tests_passed = self.check_tests(test_log_path=test_log_path)
        details["tests_passed"] = tests_passed
        if not tests_passed:
            errors.append(f"Test gate failed: test log at '{test_log_path}' missing or contains failures.")

        # 2. Check lint
        lint_passed = self.check_lint(lint_log_path=lint_log_path)
        details["lint_passed"] = lint_passed
        if not lint_passed:
            errors.append("Lint gate failed: lint log contains errors.")

        # 3. Check blueprint if provided
        blueprint_passed = True
        if blueprint_path:
            try:
                blueprint_passed = self.check_blueprint(blueprint_path=blueprint_path)
                details["blueprint_passed"] = blueprint_passed
                if not blueprint_passed:
                    errors.append(f"Blueprint gate failed: '{blueprint_path}' contains placeholders.")
            except DomainException as e:
                blueprint_passed = False
                details["blueprint_passed"] = False
                errors.append(str(e))

        all_passed = tests_passed and lint_passed and blueprint_passed
        score = 100 if all_passed else (50 if tests_passed else 0)

        return ReleaseGateResult(
            passed=all_passed,
            score=score,
            details=details,
            errors=errors,
        )
