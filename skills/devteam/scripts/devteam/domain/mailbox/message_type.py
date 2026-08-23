"""Message type + state value objects (enums as frozensets)."""

from __future__ import annotations

from ..errors import DevTeamError, ErrorCode

TYPES = frozenset(
    {"task", "status", "msg", "review-request", "blocker", "handoff", "lock"}
)
STATES = frozenset({"", "queued", "in_progress", "blocked", "done", "fail"})


def check_type(t: str) -> str:
    if t not in TYPES:
        raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"bad type {t!r}", {"allowed": sorted(TYPES)})
    return t


def check_state(s: str) -> str:
    if s not in STATES:
        raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"bad state {s!r}", {"allowed": sorted(STATES)})
    return s
