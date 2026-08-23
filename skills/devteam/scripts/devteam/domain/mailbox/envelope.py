"""Envelope entity — one mailbox message. Self-validating, path-safe."""

from __future__ import annotations

import ntpath
import posixpath
from dataclasses import asdict, dataclass

from ..errors import DevTeamError, ErrorCode
from .message_type import check_state, check_type

_ALLOWED_KEYS = {
    "id", "from", "to", "ts", "type",
    "task_id", "title", "body", "state", "evidence",
}


def _reject_absolute(p: str) -> str:
    if not p:
        return p
    norm = p.replace("\\", "/")
    if posixpath.isabs(norm) or ntpath.isabs(p) or ".." in norm.split("/"):
        raise DevTeamError(ErrorCode.ABSOLUTE_PATH, f"absolute/escaping path {p!r}")
    return p


@dataclass(frozen=True)
class Envelope:
    id: str
    frm: str
    to: str
    ts: str
    type: str
    task_id: str = ""
    title: str = ""
    body: str = ""
    state: str = ""
    evidence: str = ""

    def validate(self) -> "Envelope":
        if not self.frm or not self.to:
            raise DevTeamError(ErrorCode.SCHEMA_INVALID, "from/to required")
        check_type(self.type)
        check_state(self.state)
        _reject_absolute(self.evidence)
        return self

    def to_dict(self) -> dict:
        d = asdict(self)
        d["from"] = d.pop("frm")
        return d

    @staticmethod
    def from_dict(d: dict) -> "Envelope":
        extra = set(d) - _ALLOWED_KEYS
        if extra:
            raise DevTeamError(ErrorCode.SCHEMA_INVALID, f"unknown keys {sorted(extra)}")
        if "from" not in d or "to" not in d or "type" not in d:
            raise DevTeamError(ErrorCode.SCHEMA_INVALID, "missing from/to/type")
        return Envelope(
            id=d.get("id", ""),
            frm=d["from"],
            to=d["to"],
            ts=d.get("ts", ""),
            type=d["type"],
            task_id=d.get("task_id", ""),
            title=d.get("title", ""),
            body=d.get("body", ""),
            state=d.get("state", ""),
            evidence=d.get("evidence", ""),
        ).validate()
