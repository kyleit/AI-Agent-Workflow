from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from workflow_runtime.domain.workflow.value_objects import ArtifactPath


@dataclass
class Screenshot:
    image_id: str
    file_path: ArtifactPath
    width: int
    height: int
    device_scale_factor: float = 1.0
    captured_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def dimensions(self) -> tuple[int, int]:
        return (self.width, self.height)


@dataclass
class VisualDiff:
    baseline_id: str
    candidate_id: str
    diff_ratio: float
    mismatch_pixels: int
    diff_image_path: ArtifactPath

    def is_acceptable(self, threshold: float) -> bool:
        return self.diff_ratio <= threshold


@dataclass
class A11YReport:
    report_id: str
    violations_count: int
    passed_checks: int
    details: list[dict[str, Any]] = field(default_factory=list[dict[str, Any]])

    def compliance_score(self) -> float:
        total = self.passed_checks + self.violations_count
        if total == 0:
            return 100.0
        return (self.passed_checks / total) * 100.0

    def is_passing(self) -> bool:
        return self.compliance_score() >= 95.0 and self.violations_count == 0
