"""Seat entity."""

from __future__ import annotations

from dataclasses import dataclass

from .role import Role
from .write_set import WriteSet


@dataclass(frozen=True)
class Seat:
    slug: str
    role: Role
    title: str
    write_set: WriteSet
    skills: tuple[str, ...]
    memory_hint: str

    @property
    def inbox_name(self) -> str:
        return f"seat-{self.slug}"
