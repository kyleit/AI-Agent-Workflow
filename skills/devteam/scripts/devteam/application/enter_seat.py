"""EnterSeatUseCase — resume-aware seat entry (charter + NEXT STEP NOW + preview)."""

from __future__ import annotations

from ..domain.ports import Clock, GitStatusProvider, RosterRepository, SeatStateRepository
from ..domain.seats.seat import Seat
from .dto import EnterSeatResult
from .poll_mail import PollMailUseCase


class EnterSeatUseCase:
    def __init__(
        self,
        roster: RosterRepository,
        seat_state: SeatStateRepository,
        git: GitStatusProvider,
        clock: Clock,
        poll: PollMailUseCase,
    ) -> None:
        self._roster = roster
        self._state = seat_state
        self._git = git
        self._clock = clock
        self._poll = poll

    def execute(self, slug: str, session_id: str = "") -> EnterSeatResult:
        roster = self._roster.load()
        seat = roster.by_slug(slug)  # UNKNOWN_SEAT if bad
        state = self._state.load(slug)
        self._state.touch_header(slug, session_id, self._clock.now_iso())
        preview = self._poll.execute(slug, advance=False)  # preview, do NOT consume
        return EnterSeatResult(
            charter=charter_text(seat),
            seat_state=(state.render() if state else ""),
            next_step_now=(state.next_step_now if state else ""),
            new_mail=[e.to_dict() for e in preview],
            git_status=self._git.short_status(),
        )


def charter_text(seat: Seat) -> str:
    return (
        f"# Charter — Seat {seat.slug} ({seat.role.value})\n"
        f"- Title: {seat.title}\n"
        f"- Write-set: {', '.join(seat.write_set.dirs)}\n"
        f"- Skills to load: {', '.join(seat.skills)}\n"
        f"- Memory hint: {seat.memory_hint}\n"
        f"- Rules: single-writer on write-set; coordinate via mailbox; "
        f"update seat-state each checkpoint.\n"
    )
