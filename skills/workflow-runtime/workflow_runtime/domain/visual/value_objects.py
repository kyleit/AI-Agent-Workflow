from dataclasses import dataclass


@dataclass(frozen=True)
class ComplianceScore:
    score: float

    def is_passing(self, min_threshold: float = 90.0) -> bool:
        return self.score >= min_threshold


@dataclass(frozen=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int

    def area(self) -> int:
        return max(0, self.width) * max(0, self.height)
