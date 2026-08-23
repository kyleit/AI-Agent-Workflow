"""FileRosterRepository — maps seats.json <-> Roster aggregate."""

from __future__ import annotations

import json
import os

from ...domain.errors import DevTeamError, ErrorCode
from ...domain.seats.role import Role
from ...domain.seats.roster import Roster
from ...domain.seats.seat import Seat
from ...domain.seats.write_set import WriteSet
from ..fs.atomic import atomic_write
from ..paths import PathResolver


class FileRosterRepository:
    def __init__(self, paths: PathResolver) -> None:
        self._p = paths

    def exists(self) -> bool:
        return os.path.exists(self._p.seats_json())

    def load(self) -> Roster:
        path = self._p.seats_json()
        if not os.path.exists(path):
            raise DevTeamError(ErrorCode.NOT_INITIALIZED, "seats.json not found; run init")
        try:
            data = json.loads(open(path, encoding="utf-8-sig").read())
        except json.JSONDecodeError as e:
            raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"seats.json invalid JSON: {e}")
        seats = tuple(
            Seat(
                slug=s["slug"],
                role=Role(s["role"]),
                title=s.get("title", ""),
                write_set=WriteSet(tuple(s.get("write_set", []))),
                skills=tuple(s.get("skills", [])),
                memory_hint=s.get("memory_hint", ""),
            )
            for s in data.get("seats", [])
        )
        return Roster(
            version=int(data.get("version", 1)),
            project_id=data.get("project_id", ""),
            generated_at=data.get("generated_at", ""),
            seats=seats,
        ).validate()

    def save(self, roster: Roster) -> str:
        roster.validate()
        data = {
            "version": roster.version,
            "project_id": roster.project_id,
            "generated_at": roster.generated_at,
            "seats": [
                {
                    "slug": s.slug,
                    "role": s.role.value,
                    "title": s.title,
                    "write_set": list(s.write_set.dirs),
                    "skills": list(s.skills),
                    "memory_hint": s.memory_hint,
                }
                for s in roster.seats
            ],
        }
        atomic_write(self._p.seats_json(), json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return self._p.rel(self._p.seats_json())
