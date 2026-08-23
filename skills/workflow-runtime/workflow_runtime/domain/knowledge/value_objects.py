from dataclasses import dataclass
from enum import Enum


class MemoryScope(Enum):
    SESSION = "SESSION"
    PROJECT = "PROJECT"
    GLOBAL = "GLOBAL"


@dataclass(frozen=True)
class RelevanceScore:
    value: float

    def validate(self) -> bool:
        return 0.0 <= self.value <= 1.0
