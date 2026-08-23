"""SeatState entity — the living external memory of a seat.

The most important field is ``next_step_now`` — printed verbatim on seat entry
so a fresh session resumes with zero knowledge loss.
"""

from __future__ import annotations

from dataclasses import dataclass

_HEADINGS = [
    ("doing", "Đang làm (tới bước nào)"),
    ("decided", "Đã chốt — KHÔNG làm lại"),
    ("wip_files", "File đang dở (write-set đã đụng)"),
    ("blocked", "Chờ / blocked"),
    ("next_step_now", "BƯỚC TIẾP THEO NGAY"),
    ("doc_pointers", "Con trỏ tài liệu (blueprint/report)"),
]


@dataclass(frozen=True)
class SeatState:
    slug: str
    updated: str
    session_id: str
    status_line: str = ""
    doing: str = ""
    decided: str = ""
    wip_files: str = ""
    blocked: str = ""
    next_step_now: str = ""
    doc_pointers: str = ""

    def render(self) -> str:
        lines = [
            f"# Seat {self.slug} — Living State",
            f"- Updated: {self.updated}   - Session id: {self.session_id}   - Trạng thái: {self.status_line}",
            "",
        ]
        for attr, heading in _HEADINGS:
            lines.append(f"## {heading}")
            lines.append(getattr(self, attr))
            lines.append("")
        return "\n".join(lines).rstrip("\n") + "\n"

    @staticmethod
    def headings() -> list[tuple[str, str]]:
        return list(_HEADINGS)
