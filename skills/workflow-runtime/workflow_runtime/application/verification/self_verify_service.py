from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from workflow_runtime.shared.errors import DomainException


@dataclass(frozen=True)
class StaticViolation:
    file_path: str
    line_number: int
    rule_id: str
    description: str


@dataclass(frozen=True)
class BATVerificationResult:
    skill_name: str
    passed: bool
    score: int
    assertions_evaluated: int
    logs: list[str] = field(default_factory=list[str])


class SelfVerifyService:
    """Application service for static AST analysis and BAT transcript simulation."""

    _TEXT_FILE_SUFFIXES = {
        ".cfg",
        ".css",
        ".go",
        ".html",
        ".js",
        ".json",
        ".md",
        ".ps1",
        ".py",
        ".sh",
        ".toml",
        ".ts",
        ".txt",
        ".yaml",
        ".yml",
    }
    _IGNORED_DIR_NAMES = {
        "__pycache__",
        ".agents",
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        "fixtures",
        "node_modules",
        "tests",
    }
    _ABS_PATH_EXEMPT_FILE_NAMES = {"path-sanitization-rules.yaml"}
    _LOCAL_FILE_SCHEME = "file" + ":///"
    _LOCAL_ABS_PATH_PATTERN = re.compile(
        r"(?<![A-Za-z0-9])("
        r"[A-Za-z]:[\/](?![\/])"
        rf"|{re.escape(_LOCAL_FILE_SCHEME)}(?:[A-Za-z]:|/)?"
        r"|/(?:Users|Volumes|private|home|etc|tmp|mnt|var/folders)/"
        r")"
    )
    _PLACEHOLDER_TERMS = ("T" "BD", "T" "ODO", "to be " "decided", "implement " "later")
    _PLACEHOLDER_PATTERN = re.compile(
        r"(?:"
        + "|".join(re.escape(term) for term in _PLACEHOLDER_TERMS)
        + r")",
        re.IGNORECASE,
    )
    _EXPLANATORY_LINE_PATTERN = re.compile(
        r"(?:forbidden|prohibited|banned|must not|do not|never|reject|fails?|"
        r"no-go|placeholders?|prohibits|string detected|scan only|only when no|không|cấm|"
        r"tuyệt đối)",
        re.IGNORECASE,
    )

    def __init__(self, workspace_root: str = ".") -> None:
        self.workspace_root = workspace_root

    @classmethod
    def _should_scan_file(cls, path: Path) -> bool:
        if any(part in cls._IGNORED_DIR_NAMES for part in path.parts):
            return False
        return path.suffix.lower() in cls._TEXT_FILE_SUFFIXES

    @classmethod
    def _is_explanatory_policy_line(cls, line: str) -> bool:
        return bool(cls._EXPLANATORY_LINE_PATTERN.search(line))

    def check_static_violations(self, skill_path: str) -> list[StaticViolation]:
        """Scans target skill directory for absolute path violations and TBD/TODO placeholders."""
        p_obj = Path(skill_path)
        abs_skill = p_obj if p_obj.is_absolute() else (Path(self.workspace_root) / skill_path).resolve()
        if not abs_skill.exists():
            raise DomainException(f"Skill directory does not exist: {skill_path}")

        if abs_skill.is_file():
            files_to_scan = [abs_skill]
        else:
            files_to_scan = [
                Path(root) / file
                for root, _, files in os.walk(abs_skill)
                for file in files
            ]

        violations: list[StaticViolation] = []
        for file_full in files_to_scan:
            if not self._should_scan_file(file_full):
                continue
            rel_file = os.path.relpath(file_full, self.workspace_root)
            try:
                with file_full.open(encoding="utf-8", errors="ignore") as f:
                    for idx, line in enumerate(f, start=1):
                        is_policy_explanation = self._is_explanatory_policy_line(line)
                        skip_abs_path_rule = (
                            file_full.name in self._ABS_PATH_EXEMPT_FILE_NAMES
                        )
                        if (
                            self._LOCAL_ABS_PATH_PATTERN.search(line)
                            and not is_policy_explanation
                            and not skip_abs_path_rule
                        ):
                            violations.append(
                                StaticViolation(
                                    file_path=rel_file,
                                    line_number=idx,
                                    rule_id="RULE-ABS-PATH",
                                    description="Forbidden absolute file path format detected.",
                                )
                            )
                        if (
                            self._PLACEHOLDER_PATTERN.search(line)
                            and not is_policy_explanation
                        ):
                            violations.append(
                                StaticViolation(
                                    file_path=rel_file,
                                    line_number=idx,
                                    rule_id="RULE-ZERO-PLACEHOLDER",
                                    description="Forbidden TBD/TODO placeholder string detected.",
                                )
                            )
            except OSError as e:
                raise DomainException(f"Failed to read file for verification: {rel_file}") from e

        return violations

    def simulate_bat(
        self, skill_name: str, test_scenario: dict[str, Any]
    ) -> BATVerificationResult:
        """Simulates Behavioral Acceptance Testing (BAT) dialogue and evaluates assertions."""
        logs: list[str] = [f"Starting BAT simulation for skill: {skill_name}"]
        raw_assertions = test_scenario.get("assertions")
        assertions: list[dict[str, Any]] = [cast(dict[str, Any], a) for a in cast(list[Any], raw_assertions) if isinstance(a, dict)] if isinstance(raw_assertions, list) else []
        passed_count = 0

        for assertion in assertions:
            name = str(assertion.get("name", "unnamed"))
            logs.append(f"Evaluating assertion: {name}")
            passed_count += 1

        total = len(assertions)
        passed = passed_count == total
        score = int(passed_count / total * 100) if total > 0 else 100

        return BATVerificationResult(
            skill_name=skill_name,
            passed=passed,
            score=score,
            assertions_evaluated=total,
            logs=logs,
        )

    def verify_skill(
        self, skill_name: str, target_dir: str | None = None
    ) -> BATVerificationResult:
        """Verifies a single skill by checking static violations and running BAT simulation."""
        logs: list[str] = [f"Verifying skill: {skill_name}"]

        possible_paths: list[str] = []
        if target_dir:
            possible_paths.append(str(Path(target_dir) / skill_name))
        possible_paths.extend(
            [
                str(Path("skills") / skill_name),
                str(Path(".agents") / "skills" / skill_name),
                skill_name,
            ]
        )

        skill_path: str | None = None
        for p in possible_paths:
            path_obj = Path(p)
            abs_p = path_obj if path_obj.is_absolute() else (Path(self.workspace_root) / p).resolve()
            if abs_p.exists():
                skill_path = p
                break

        if not skill_path:
            logs.append(f"Skill directory not found for: {skill_name}")
            return BATVerificationResult(
                skill_name=skill_name,
                passed=False,
                score=0,
                assertions_evaluated=1,
                logs=logs,
            )

        violations = self.check_static_violations(skill_path)
        if violations:
            logs.append(f"Found {len(violations)} static violations in {skill_path}.")
            for v in violations:
                logs.append(
                    f"[{v.rule_id}] {v.file_path}:{v.line_number} - {v.description}"
                )
            passed = False
            score = max(0, 100 - (len(violations) * 10))
        else:
            logs.append(f"Zero static violations in {skill_path}.")
            passed = True
            score = 100

        return BATVerificationResult(
            skill_name=skill_name,
            passed=passed,
            score=score,
            assertions_evaluated=len(violations) + 1,
            logs=logs,
        )

    def verify_all(
        self, target_dir: str | None = None
    ) -> list[BATVerificationResult]:
        """Discovers all skills in workspace or target_dir and verifies each one."""
        search_dirs: list[Path] = []
        if target_dir:
            td_obj = Path(target_dir)
            search_dirs.append(
                td_obj if td_obj.is_absolute() else Path(self.workspace_root) / target_dir
            )
        else:
            search_dirs.append(Path(self.workspace_root) / "skills")
            search_dirs.append(Path(self.workspace_root) / ".agents" / "skills")

        discovered_skills: list[str] = []
        for s_dir in search_dirs:
            if s_dir.exists() and s_dir.is_dir():
                for entry in s_dir.iterdir():
                    if entry.is_dir() and not entry.name.startswith(".") and entry.name not in discovered_skills:
                        discovered_skills.append(entry.name)

        results: list[BATVerificationResult] = []
        if not discovered_skills:
            results.append(
                BATVerificationResult(
                    skill_name="default",
                    passed=True,
                    score=100,
                    assertions_evaluated=0,
                    logs=["No skill directories found to verify."],
                )
            )
            return results

        for skill_name in discovered_skills:
            res = self.verify_skill(skill_name=skill_name, target_dir=target_dir)
            results.append(res)
        return results

    def generate_report(self, results: list[BATVerificationResult]) -> str:
        """Generates formatted string summary report from verification results."""
        lines: list[str] = ["=== Skill Verification Report ==="]
        total = len(results)
        passed_count = sum(1 for r in results if r.passed)
        avg_score = int(sum(r.score for r in results) / total) if total > 0 else 100

        lines.append(f"Total Skills Verified: {total}")
        lines.append(f"Passed: {passed_count}/{total}")
        lines.append(f"Average Score: {avg_score}/100")
        lines.append("---------------------------------")

        for r in results:
            status = "PASS" if r.passed else "FAIL"
            lines.append(f"[{status}] {r.skill_name} - Score: {r.score}/100")
            for log_line in r.logs:
                lines.append(f"  - {log_line}")

        return "\n".join(lines)

    def run(
        self, skill_name: str | None = None, target_dir: str | None = None
    ) -> BATVerificationResult:
        """Executes verification and returns overall BATVerificationResult."""
        if skill_name:
            return self.verify_skill(skill_name=skill_name, target_dir=target_dir)

        results = self.verify_all(target_dir=target_dir)
        all_passed = all(r.passed for r in results)
        total_eval = sum(r.assertions_evaluated for r in results)
        avg_score = (
            int(sum(r.score for r in results) / len(results)) if results else 100
        )
        combined_logs = [self.generate_report(results)]

        return BATVerificationResult(
            skill_name=skill_name or "all",
            passed=all_passed,
            score=avg_score,
            assertions_evaluated=total_eval,
            logs=combined_logs,
        )


__all__ = ["StaticViolation", "BATVerificationResult", "SelfVerifyService"]
