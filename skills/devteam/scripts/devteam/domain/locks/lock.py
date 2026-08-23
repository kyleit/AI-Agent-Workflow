"""Lock entity — a seat's hold on a repo-relative resource path."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Lock:
    path: str            # repo-relative resource path
    holder: str          # seat slug holding it
    ts: str              # ISO acquired-at
    note: str = ""
    expires_at: str = ""  # ISO; "" = no expiry

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "holder": self.holder,
            "ts": self.ts,
            "note": self.note,
            "expires_at": self.expires_at,
        }
