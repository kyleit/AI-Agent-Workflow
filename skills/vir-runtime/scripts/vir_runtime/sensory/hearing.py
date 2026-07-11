# File path: vir_runtime/sensory/hearing.py
from typing import Optional, List, Dict, Any
from vir_runtime.core.bus import AsyncEventBus, Event

class HearingEngine:
    def __init__(self, bus: AsyncEventBus, adapter: Optional[Any] = None):
        self.bus = bus
        self.adapter = adapter
        self.listening = False
        self.logs: List[Dict[str, Any]] = []

    def start_listening(self) -> None:
        """Attach listeners to capture console and network event streams."""
        self.listening = True
        print("[HearingEngine] Started listening for console and network logs.")
        # If adapter supports console hooks, register them here
        # For now, we simulate capturing a log event
        self.log_console_event("error", "Refused to load stylesheet because of MIME type.")

    def stop_listening(self) -> None:
        """Stop listening for event streams."""
        self.listening = False
        print("[HearingEngine] Stopped listening.")

    def log_console_event(self, level: str, message: str) -> None:
        """Register and publish console log finding."""
        if not self.listening:
            return
            
        log_payload = {
            "level": level,
            "message": message,
            "domain": "console"
        }
        self.logs.append(log_payload)
        
        # Publish event to bus
        event = Event(
            topic=f"vir.hearing.console.{level}",
            payload=log_payload
        )
        self.bus.publish(event)
