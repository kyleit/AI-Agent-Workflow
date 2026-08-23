from dataclasses import dataclass
from typing import Any


@dataclass
class PacketEnvelope:
    version: str
    type: str
    timestamp: int
    payload: Any
    session_id: str = ""
