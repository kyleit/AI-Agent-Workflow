"""Cursor value object — how many inbox lines a seat has consumed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Cursor:
    value: int

    def advanced_by(self, n: int) -> "Cursor":
        return Cursor(self.value + n)
