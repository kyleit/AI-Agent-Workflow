"""FileSeatStateRepository — render/parse the living seat-state markdown."""

from __future__ import annotations

import os
import re

from ...domain.handoff.seat_state import SeatState
from ..fs.atomic import atomic_write
from ..paths import PathResolver

_HEADER = re.compile(
    r"- Updated:\s*(?P<updated>.*?)\s{2,}- Session id:\s*(?P<sid>.*?)\s{2,}- Trạng thái:\s*(?P<status>.*)"
)


class FileSeatStateRepository:
    def __init__(self, paths: PathResolver) -> None:
        self._p = paths

    def load(self, slug: str) -> SeatState | None:
        path = self._p.seat_state(slug)
        if not os.path.exists(path):
            return None
        text = open(path, encoding="utf-8").read()
        updated = sid = status = ""
        m = _HEADER.search(text)
        if m:
            updated, sid, status = m.group("updated"), m.group("sid"), m.group("status")
        sections = self._split_sections(text)
        return SeatState(
            slug=slug,
            updated=updated,
            session_id=sid,
            status_line=status,
            **{attr: sections.get(heading, "") for attr, heading in SeatState.headings()},
        )

    def save(self, state: SeatState) -> str:
        atomic_write(self._p.seat_state(state.slug), state.render())
        return self._p.rel(self._p.seat_state(state.slug))

    def touch_header(self, slug: str, session_id: str, updated: str) -> None:
        existing = self.load(slug)
        if existing is None:
            base = SeatState(slug=slug, updated=updated, session_id=session_id)
        else:
            base = SeatState(
                slug=slug,
                updated=updated,
                session_id=session_id or existing.session_id,
                status_line=existing.status_line,
                doing=existing.doing,
                decided=existing.decided,
                wip_files=existing.wip_files,
                blocked=existing.blocked,
                next_step_now=existing.next_step_now,
                doc_pointers=existing.doc_pointers,
            )
        self.save(base)

    @staticmethod
    def _split_sections(text: str) -> dict:
        out: dict[str, str] = {}
        current = None
        buf: list[str] = []
        for line in text.splitlines():
            if line.startswith("## "):
                if current is not None:
                    out[current] = "\n".join(buf).strip()
                current = line[3:].strip()
                buf = []
            elif current is not None:
                buf.append(line)
        if current is not None:
            out[current] = "\n".join(buf).strip()
        return out
