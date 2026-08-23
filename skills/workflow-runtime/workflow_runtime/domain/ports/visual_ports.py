from dataclasses import dataclass
from typing import Any, Dict, List, Protocol


class VisualEvent:
    def __init__(self, topic: str, payload: Dict[str, Any], source: str = ""):
        self.topic = topic
        self.payload = payload
        self.source = source

class AsyncEventBusPort(Protocol):
    async def publish(self, event: VisualEvent) -> None:
        ...

@dataclass
class ConsensusRecord:
    verdict: str
    confidence_breakdowns: Dict[str, float]
    vetoes: List[str]
    evidence_ids: List[str]
