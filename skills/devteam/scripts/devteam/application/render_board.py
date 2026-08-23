"""RenderBoardUseCase — build the seat status board + active locks section."""

from __future__ import annotations

import datetime

from ..domain.locks.policy import is_expired
from ..domain.ports import BoardRepository, Clock, LockRepository, RosterRepository, SeatStateRepository


class RenderBoardUseCase:
    def __init__(
        self,
        roster: RosterRepository,
        seat_state: SeatStateRepository,
        board: BoardRepository,
        locks: LockRepository,
        clock: Clock,
    ) -> None:
        self._roster = roster
        self._state = seat_state
        self._board = board
        self._locks = locks
        self._clock = clock

    def execute(self, write: bool = False) -> str:
        roster = self._roster.load()
        states = {s.slug: self._state.load(s.slug) for s in roster.seats}
        content = self._board.render(roster, states)
        content = content.rstrip("\n") + "\n\n" + self._locks_section()
        if write:
            self._board.write(content)
        return content

    def _locks_section(self) -> str:
        locks = self._locks.all()
        if not locks:
            return "## Active locks\n(none)\n"
        now = datetime.datetime.fromisoformat(self._clock.now_iso())
        lines = [
            "## Active locks",
            "",
            "| Path | Holder | Expires | State |",
            "|------|--------|---------|-------|",
        ]
        for lock in locks:
            state = "expired" if is_expired(lock, now) else "held"
            expires = lock.expires_at or "—"
            lines.append(f"| `{lock.path}` | {lock.holder} | {expires} | {state} |")
        lines.append("")
        return "\n".join(lines)
