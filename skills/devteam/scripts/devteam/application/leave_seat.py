"""LeaveSeatUseCase — persist the living seat-state (handoff) from given fields."""

from __future__ import annotations

from ..domain.handoff.seat_state import SeatState
from ..domain.ports import BoardRepository, Clock, RosterRepository, SeatStateRepository


class LeaveSeatUseCase:
    def __init__(
        self,
        roster: RosterRepository,
        seat_state: SeatStateRepository,
        board: BoardRepository,
        clock: Clock,
    ) -> None:
        self._roster = roster
        self._state = seat_state
        self._board = board
        self._clock = clock

    def execute(self, slug: str, fields: dict, session_id: str = "") -> str:
        roster = self._roster.load()
        roster.by_slug(slug)  # UNKNOWN_SEAT if bad
        prev = self._state.load(slug)
        merged = {attr: fields.get(attr, getattr(prev, attr) if prev else "") for attr, _ in SeatState.headings()}
        state = SeatState(
            slug=slug,
            updated=self._clock.now_iso(),
            session_id=session_id or (prev.session_id if prev else ""),
            status_line=fields.get("status_line", prev.status_line if prev else ""),
            **merged,
        )
        path = self._state.save(state)
        # refresh board so the seat's latest next-step is visible
        states = {s.slug: self._state.load(s.slug) for s in roster.seats}
        self._board.write(self._board.render(roster, states))
        return path
