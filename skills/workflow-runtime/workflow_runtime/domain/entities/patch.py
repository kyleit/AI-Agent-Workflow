from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PatchOp:
    op: str
    path: str
    value: Any = None
    from_path: str | None = None

@dataclass
class ASTPatchPayload:
    base_version: int
    target_version: int
    patches: list[PatchOp]

@dataclass
class PacketEnvelope:
    type: str
    timestamp: str
    payload: Any
