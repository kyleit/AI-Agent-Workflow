# File path: vir_runtime/domain/evidence.py
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class Evidence:
    source_agent: str
    classification: str
    payload: Dict[str, Any]
    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: time.time())
