# File path: vir_runtime/core/ipc.py
from __future__ import annotations

import json
import sys
from typing import Any, TextIO, cast


class IPCEmitter:
    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream: TextIO = cast(TextIO, stream or sys.stdout)

    def emit_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Format investigation stage details as NDJSON envelopes and print to stdout."""
        envelope = {
            "type": event_type,
            "payload": data
        }
        envelope_str = json.dumps(envelope)
        self.stream.write(envelope_str + "\n")
        self.stream.flush()
        print(f"[IPCEmitter] Emitted event type: {event_type}")


__all__ = ["IPCEmitter"]
