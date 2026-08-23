"""Role value object."""

from __future__ import annotations

from dataclasses import dataclass

from ..errors import DevTeamError, ErrorCode

_ROLES = {"leader", "dev"}


@dataclass(frozen=True)
class Role:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _ROLES:
            raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"bad role {self.value!r}")

    @property
    def is_leader(self) -> bool:
        return self.value == "leader"
