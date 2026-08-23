"""Lock acquisition policy — pure decision function (owns the rule).

Infrastructure applies the decision atomically; this module has no I/O.
"""

from __future__ import annotations

import datetime

from .lock import Lock

GRANT = "GRANT"      # no holder — take it
REFRESH = "REFRESH"  # same holder re-acquires — update note/expiry
STEAL = "STEAL"      # forced takeover from another holder
CONFLICT = "CONFLICT"  # held by another, not expired, not forced


def is_expired(lock: Lock, now: datetime.datetime) -> bool:
    if not lock.expires_at:
        return False
    try:
        return datetime.datetime.fromisoformat(lock.expires_at) <= now
    except ValueError:
        return False


def decide(existing: Lock | None, requester: str, now: datetime.datetime, force: bool) -> str:
    if existing is None:
        return GRANT
    if existing.holder == requester:
        return REFRESH
    if is_expired(existing, now):
        return GRANT
    if force:
        return STEAL
    return CONFLICT
