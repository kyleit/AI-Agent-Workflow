"""FileBoardRepository — render the seat status board (Markdown table)."""

from __future__ import annotations

from ...domain.seats.roster import Roster
from ..fs.atomic import atomic_write
from ..paths import PathResolver


def _cell(value: str) -> str:
    one = " ".join((value or "").splitlines()).strip()
    one = one.replace("|", "\\|")
    return one[:80] if one else "—"


class FileBoardRepository:
    def __init__(self, paths: PathResolver) -> None:
        self._p = paths

    def render(self, roster: Roster, states: dict) -> str:
        lines = [
            f"# DevTeam Board — {roster.project_id}",
            "",
            f"Generated seats: {len(roster.seats)} · roster: `.agents/devteam/seats.json`",
            "",
            "| Seat | Role | Status | Updated | NEXT STEP NOW |",
            "|------|------|--------|---------|---------------|",
        ]
        for s in roster.seats:
            st = states.get(s.slug)
            status = _cell(st.status_line if st else "")
            updated = _cell(st.updated if st else "")
            nxt = _cell(st.next_step_now if st else "")
            lines.append(f"| `{s.slug}` | {s.role.value} | {status} | {updated} | {nxt} |")
        lines.append("")
        return "\n".join(lines)

    def write(self, content: str) -> str:
        atomic_write(self._p.board(), content if content.endswith("\n") else content + "\n")
        return self._p.rel(self._p.board())
