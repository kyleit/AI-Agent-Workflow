"""Visual domain."""

from workflow_runtime.domain.visual.entities import (A11YReport, Screenshot,
                                                     VisualDiff)
from workflow_runtime.domain.visual.repositories import IVisualRepository
from workflow_runtime.domain.visual.value_objects import (BoundingBox,
                                                          ComplianceScore)

__all__ = [
    "A11YReport",
    "BoundingBox",
    "ComplianceScore",
    "IVisualRepository",
    "Screenshot",
    "VisualDiff",
]
