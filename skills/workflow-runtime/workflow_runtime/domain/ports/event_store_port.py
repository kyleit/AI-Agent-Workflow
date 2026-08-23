from typing import Any, Dict, Protocol


class EventStorePort(Protocol):
    def append_event(self, aggregate_id: str, event_type: str, payload: Dict[str, Any]) -> None:
        ...

    def get_events(self, aggregate_id: str) -> list[Dict[str, Any]]:
        ...
