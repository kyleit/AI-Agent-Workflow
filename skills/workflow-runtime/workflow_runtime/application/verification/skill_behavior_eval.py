from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class BehaviorAssertion:
    name: str
    pattern: str
    mode: str = "contains"


@dataclass(frozen=True)
class BehaviorScenario:
    scenario_id: str
    prompt: str
    pressure_types: Sequence[str]
    response_fixture: str
    required_patterns: Sequence[BehaviorAssertion]
    forbidden_patterns: Sequence[BehaviorAssertion]


@dataclass(frozen=True)
class BehaviorEvalResult:
    passed: bool
    score: int
    assertions_evaluated: int
    failures: list[str] = field(default_factory=list[str])
    evidence: list[str] = field(default_factory=list[str])


class SkillBehaviorEvalService:
    """Evaluate declarative skill behavior fixtures without executing them."""

    def discover_manifests(self, skill_dir: Path) -> list[Path]:
        evals_dir = skill_dir / "evals"
        if not evals_dir.is_dir():
            return []
        return sorted(path for path in evals_dir.glob("*.json") if path.is_file())

    def evaluate_skill(self, skill_dir: Path) -> BehaviorEvalResult:
        manifests = self.discover_manifests(skill_dir)
        if not manifests:
            return BehaviorEvalResult(True, 100, 0, [], ["behavioral_evals_absent"])
        results = [self.evaluate_manifest(path) for path in manifests]
        failures = [failure for result in results for failure in result.failures]
        evidence = [item for result in results for item in result.evidence]
        total = sum(result.assertions_evaluated for result in results)
        score = int((max(0, total - len(failures)) / total) * 100) if total else 100
        return BehaviorEvalResult(not failures, score, total, failures, evidence)

    def evaluate_manifest(self, path: Path) -> BehaviorEvalResult:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return BehaviorEvalResult(False, 0, 1, [f"{path.as_posix()}: invalid manifest: {exc}"], [path.as_posix()])
        scenarios = data.get("scenarios") if isinstance(data, dict) else None
        if not isinstance(scenarios, list):
            return BehaviorEvalResult(False, 0, 1, [f"{path.as_posix()}: scenarios must be a list"], [path.as_posix()])
        failures: list[str] = []
        total = 0
        for raw in scenarios:
            if not isinstance(raw, dict):
                failures.append(f"{path.as_posix()}: scenario must be an object")
                total += 1
                continue
            scenario_id = str(raw.get("scenario_id", "unnamed"))
            response = str(raw.get("response_fixture", ""))
            for assertion in self._assertions(raw.get("required_patterns")):
                total += 1
                if not self._matches(assertion, response):
                    failures.append(f"{scenario_id}:{assertion.name}: required pattern missing")
            for assertion in self._assertions(raw.get("forbidden_patterns")):
                total += 1
                if self._matches(assertion, response):
                    failures.append(f"{scenario_id}:{assertion.name}: forbidden pattern present")
        score = int(((total - len(failures)) / total) * 100) if total else 100
        return BehaviorEvalResult(not failures, score, total, failures, [path.as_posix()])

    def _assertions(self, raw_assertions: object) -> Sequence[BehaviorAssertion]:
        if not isinstance(raw_assertions, list):
            return tuple()
        return tuple(
            BehaviorAssertion(
                name=str(item.get("name", "unnamed")),
                pattern=str(item.get("pattern", "")),
                mode=str(item.get("mode", "contains")),
            )
            for item in raw_assertions
            if isinstance(item, dict)
        )

    def _matches(self, assertion: BehaviorAssertion, response: str) -> bool:
        if assertion.mode == "regex":
            return re.search(assertion.pattern, response, re.IGNORECASE) is not None
        return assertion.pattern.lower() in response.lower()


__all__ = [
    "BehaviorAssertion",
    "BehaviorEvalResult",
    "BehaviorScenario",
    "SkillBehaviorEvalService",
]
