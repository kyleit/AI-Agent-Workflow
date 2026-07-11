# File path: vir_runtime/core/ipc.py
import json
import sys
from typing import Dict, Any

class IPCEmitter:
    def __init__(self, stream=None):
        # Allow passing custom stream for test cases isolation
        self.stream = stream or sys.stdout

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Format investigation stage details as NDJSON envelopes and print to stdout."""
        envelope = {
            "type": event_type,
            "payload": data
        }
        envelope_str = json.dumps(envelope)
        self.stream.write(envelope_str + "\n")
        self.stream.flush()
        print(f"[IPCEmitter] Emitted event type: {event_type}")
