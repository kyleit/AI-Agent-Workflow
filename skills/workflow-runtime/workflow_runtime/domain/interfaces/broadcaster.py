from abc import ABC, abstractmethod
from typing import Any, Callable


class IHMRBroadcaster(ABC):
    @abstractmethod
    async def start(self) -> None:
        pass

    @abstractmethod
    async def broadcast(self, payload: Any) -> None:
        pass

    @abstractmethod
    def on_client_message(self, callback: Callable[[str, Any], None]) -> None:
        pass
