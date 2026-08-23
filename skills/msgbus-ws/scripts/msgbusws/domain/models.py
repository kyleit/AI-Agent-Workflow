"""Domain value objects: Message, FileMeta, UploadSession."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """A bus message. `to` empty/None => broadcast; otherwise private to that peer."""

    seq: int
    ts: str
    sender: str  # serialized as "from" on the wire
    to: str | None
    text: str

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"seq": self.seq, "ts": self.ts, "from": self.sender, "text": self.text}
        if self.to:
            data["to"] = self.to
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            seq=int(data.get("seq", 0)),
            ts=str(data.get("ts", "")),
            sender=str(data.get("from", data.get("sender", ""))),
            to=(data.get("to") or None),
            text=str(data.get("text", "")),
        )


@dataclass
class FileMeta:
    name: str
    size: int
    ts: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "size": self.size, "ts": self.ts}


@dataclass
class UploadSession:
    """A resumable (tus) upload in progress."""

    upload_id: str
    name: str
    sender: str
    to: str | None
    length: int
    offset: int = 0

    @property
    def complete(self) -> bool:
        return self.offset >= self.length

    def to_dict(self) -> dict[str, Any]:
        return {
            "upload_id": self.upload_id,
            "name": self.name,
            "sender": self.sender,
            "to": self.to,
            "length": self.length,
            "offset": self.offset,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UploadSession":
        return cls(
            upload_id=str(data["upload_id"]),
            name=str(data["name"]),
            sender=str(data.get("sender", "")),
            to=(data.get("to") or None),
            length=int(data["length"]),
            offset=int(data.get("offset", 0)),
        )
