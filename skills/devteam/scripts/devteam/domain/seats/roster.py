"""Roster aggregate — the set of seats, with cross-seat invariants."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..errors import DevTeamError, ErrorCode
from .seat import Seat

_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")


@dataclass(frozen=True)
class Roster:
    version: int
    project_id: str
    generated_at: str
    seats: tuple[Seat, ...]

    def validate(self) -> "Roster":
        leaders = [s for s in self.seats if s.role.is_leader]
        if len(leaders) != 1:
            raise DevTeamError(
                ErrorCode.DUPLICATE_LEADER,
                f"exactly one leader required, got {len(leaders)}",
            )
        seen: set[str] = set()
        for s in self.seats:
            if not _SLUG.match(s.slug):
                raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"bad slug {s.slug!r}")
            if s.slug in seen:
                raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"duplicate slug {s.slug!r}")
            seen.add(s.slug)
        for i, a in enumerate(self.seats):
            for b in self.seats[i + 1:]:
                if a.write_set.overlaps(b.write_set):
                    raise DevTeamError(
                        ErrorCode.WRITESET_OVERLAP,
                        f"write-sets overlap: {a.slug} vs {b.slug}",
                        {"a": a.slug, "b": b.slug},
                    )
        return self

    def leader(self) -> Seat:
        return next(s for s in self.seats if s.role.is_leader)

    def by_slug(self, slug: str) -> Seat:
        for s in self.seats:
            if s.slug == slug:
                return s
        raise DevTeamError(ErrorCode.UNKNOWN_SEAT, f"no seat {slug!r}")
