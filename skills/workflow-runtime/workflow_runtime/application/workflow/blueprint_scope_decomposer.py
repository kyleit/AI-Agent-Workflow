from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class BlueprintScopeAssessment:
    requires_phase_split: bool
    recommended_phase_count: int
    reasons: list[str] = field(default_factory=list[str])
    required_artifacts: list[str] = field(default_factory=list[str])
    boundary_plan: list[str] = field(default_factory=list[str])


class BlueprintScopeDecomposer:
    _requirement_pattern = re.compile(r"\b(?:FR|NFR|AC|G|US)-\d+\b", re.IGNORECASE)
    _file_row_pattern = re.compile(r"^\s*\|\s*[^|]+\|\s*[^|]+\|\s*(?:NEW|MODIFY|DELETE|\[NEW\]|\[MODIFY\]|\[DELETE\])\s*\|", re.IGNORECASE)
    _task_row_pattern = re.compile(r"^\s*\|\s*\d+\s*\|", re.IGNORECASE)

    def infer_from_blueprint(self, blueprint_text: str) -> dict[str, object]:
        """Derive planning complexity when the caller has no structured metrics.

        Blueprint validation must judge the artifact that was actually written,
        rather than trusting an omitted or stale ``declared_phase_count``.
        Counts are deliberately conservative: duplicate requirement references
        are collapsed, while file and task rows represent implementation work.
        """
        requirements = {
            match.group(0).upper()
            for match in self._requirement_pattern.finditer(blueprint_text)
        }
        file_rows = [
            line for line in blueprint_text.splitlines()
            if self._file_row_pattern.search(line)
        ]
        task_rows = [
            line for line in blueprint_text.splitlines()
            if self._task_row_pattern.search(line)
        ]
        layer_markers = {
            "domain", "application", "infrastructure", "delivery",
            "presentation", "frontend", "backend",
        }
        lower_text = blueprint_text.lower()
        cross_layer = sum(marker in lower_text for marker in layer_markers) >= 4
        return {
            "capability_count": len(requirements),
            "file_family_count": len(file_rows),
            "task_count": len(task_rows),
            "cross_layer": cross_layer,
            "line_count": len(blueprint_text.splitlines()),
        }

    def assess(
        self,
        capability_count: int,
        file_family_count: int,
        task_count: int,
        cross_layer: bool,
        boundary_kinds: Sequence[str] | None = None,
    ) -> BlueprintScopeAssessment:
        reasons: list[str] = []
        phase_count = 1
        boundary_plan = [item.strip() for item in (boundary_kinds or ()) if item.strip()]
        if capability_count > 7:
            reasons.append("capability_threshold_exceeded")
            phase_count = max(phase_count, 3)
        elif capability_count > 3:
            phase_count = max(phase_count, 2)
        if file_family_count > 4:
            reasons.append("file_family_threshold_exceeded")
            phase_count = max(phase_count, 3)
        elif file_family_count > 2:
            phase_count = max(phase_count, 2)
        if task_count > 10:
            reasons.append("task_threshold_exceeded")
            phase_count = max(phase_count, 3)
        elif task_count > 5:
            phase_count = max(phase_count, 2)
        if cross_layer:
            reasons.append("cross_layer_scope")
            phase_count = max(phase_count, 2)
        if boundary_plan:
            phase_count = max(phase_count, len(boundary_plan))
        if not reasons and phase_count == 1:
            return BlueprintScopeAssessment(
                False, 1, [], ["master_blueprint", "phase_01_blueprint"], ["single_bounded_phase"]
            )
        if not boundary_plan:
            boundary_plan = [f"phase_{index:02d}" for index in range(1, phase_count + 1)]
        return BlueprintScopeAssessment(
            True,
            phase_count,
            reasons,
            ["master_blueprint"] + [f"phase_{index:02d}_blueprint" for index in range(1, phase_count + 1)],
            boundary_plan,
        )


__all__ = ["BlueprintScopeAssessment", "BlueprintScopeDecomposer"]
