from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import PurePath


class PhaseStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RoleId:
    value: str

    def validate(self) -> bool:
        if not self.value:
            return False
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", self.value.strip()))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ArtifactPath:
    path: str

    def is_relative(self) -> bool:
        if not self.path:
            return False
        cleaned = self.path.strip()
        if cleaned.startswith("/") or cleaned.startswith("\\"):
            return False
        return not bool(re.match(r"^[a-zA-Z]:", cleaned))

    def get_normalized(self) -> str:
        if not self.is_relative():
            raise ValueError(f"ArtifactPath must be relative, got: {self.path}")
        return PurePath(self.path).as_posix()


__all__ = [
    "PhaseStatus",
    "RoleId",
    "ArtifactPath",
]
