# File path: vir_runtime/core/loop_protector.py
import hashlib
import json
from collections import deque
from typing import Any

class LoopProtector:
    def __init__(self, max_history: int = 100, repeat_threshold: int = 3):
        self.history = deque(maxlen=max_history)
        self.repeat_threshold = repeat_threshold

    def inspect_event(self, event: Any) -> bool:
        """Inspect if the event is part of an infinite loop sequence."""
        try:
            # Create a stable hash based on topic and payload content
            serialized_payload = json.dumps(event.payload, sort_keys=True)
            hash_input = f"{event.topic}:{serialized_payload}".encode("utf-8")
            event_hash = hashlib.md5(hash_input).hexdigest()
        except Exception:
            # Fallback hash if payload cannot be serialized
            event_hash = hashlib.md5(f"{event.topic}".encode("utf-8")).hexdigest()

        # Count occurrences in recent history
        occurrences = self.history.count(event_hash)
        
        # Add to history
        self.history.append(event_hash)
        
        if occurrences >= self.repeat_threshold:
            return True # Infinite loop sequence detected
        return False
