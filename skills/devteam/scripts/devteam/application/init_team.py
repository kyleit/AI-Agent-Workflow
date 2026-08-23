"""InitTeamUseCase — propose a roster from the repo layout, then optionally apply.

Preview (apply=False) returns the proposed roster without touching disk.
Apply (apply=True) persists seats.json, charters, seat-state stubs, inboxes, board.
"""

from __future__ import annotations

from ..domain.errors import DevTeamError, ErrorCode
from ..domain.handoff.seat_state import SeatState
from ..domain.ports import (
    BoardRepository,
    Clock,
    MailboxRepository,
    RepoScanner,
    RosterRepository,
    SeatStateRepository,
)
from ..domain.seats.role import Role
from ..domain.seats.roster import Roster
from ..domain.seats.seat import Seat
from ..domain.seats.write_set import WriteSet
from .dto import InitResult


def _slugify(name: str) -> str:
    s = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
    while "--" in s:
        s = s.replace("--", "-")
    return s[:31] or "area"


class InitTeamUseCase:
    def __init__(
        self,
        roster: RosterRepository,
        mailbox: MailboxRepository,
        seat_state: SeatStateRepository,
        board: BoardRepository,
        scanner: RepoScanner,
        clock: Clock,
        project_id: str,
    ) -> None:
        self._roster = roster
        self._mailbox = mailbox
        self._state = seat_state
        self._board = board
        self._scanner = scanner
        self._clock = clock
        self._project_id = project_id

    def propose(self) -> Roster:
        now = self._clock.now_iso()
        seats = [
            Seat(
                slug="leader",
                role=Role("leader"),
                title="Team Leader / Integrator",
                write_set=WriteSet((".agents/devteam",)),
                skills=("workflow-coordinator",),
                memory_hint="architecture overview, cross-cutting rules",
            )
        ]
        used = {"leader"}
        for d in self._scanner.top_level_dirs():
            slug = _slugify(d)
            while slug in used:
                slug = slug + "-x"
            used.add(slug)
            seats.append(
                Seat(
                    slug=slug,
                    role=Role("dev"),
                    title=f"{d} owner",
                    write_set=WriteSet((d,)),
                    skills=("python-development",),
                    memory_hint=f"internals of {d}",
                )
            )
        return Roster(1, self._project_id, now, tuple(seats)).validate()

    def execute(self, apply: bool = False) -> InitResult:
        if apply and self._roster.exists():
            raise DevTeamError(
                ErrorCode.ALREADY_INITIALIZED,
                "seats.json already exists; edit it directly or remove it to re-init",
            )
        roster = self.propose()
        roster_dict = {
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
        if not apply:
            return InitResult(roster=roster_dict, applied=False)

        written: list[str] = []
        written.append(self._roster.save(roster))
        for s in roster.seats:
            self._mailbox.ensure_inbox(s.slug)
            stub = SeatState(
                slug=s.slug,
                updated=roster.generated_at,
                session_id="",
                status_line="idle — seat not yet occupied",
                next_step_now="(none yet) — first session should read the charter and pick up work.",
            )
            written.append(self._state.save(stub))
        states = {s.slug: self._state.load(s.slug) for s in roster.seats}
        written.append(self._board.write(self._board.render(roster, states)))
        return InitResult(roster=roster_dict, files_written=written, applied=True)
