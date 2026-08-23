import re
from dataclasses import dataclass
from enum import Enum


class GateStatus(Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class SemVer:
    version_str: str

    def is_valid(self) -> bool:
        if not self.version_str:
            return False
        pattern = r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$"
        return bool(re.match(pattern, self.version_str.strip()))
