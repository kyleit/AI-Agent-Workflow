from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

from workflow_runtime.domain.interfaces.broadcaster import IHMRBroadcaster


class AsyncioWebSocketBroadcaster(IHMRBroadcaster):
    def __init__(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        self.host = host
        self.port = port
        self.clients: set[Any] = set()
        self.message_callback: Callable[[str, Any], None] | None = None

    async def _handler(self, websocket: Any) -> None:
        self.clients.add(websocket)
        try:
            async for message in websocket:
                if self.message_callback:
                    try:
                        data = json.loads(str(message))
                        self.message_callback(str(id(websocket)), data)
                    except Exception:
                        pass
        finally:
            if websocket in self.clients:
                self.clients.remove(websocket)

    async def start(self) -> None:
        try:
            import websockets
            if hasattr(websockets, "serve"):
                async with websockets.serve(self._handler, self.host, self.port):  # pyright: ignore[reportGeneralTypeIssues]
                    await asyncio.Future()
        except ImportError:
            pass

    async def broadcast(self, payload: Any) -> None:
        if not self.clients:
            return
        message = json.dumps(payload, default=lambda x: getattr(x, "__dict__", str(x)))
        import websockets
        ws_broadcast: Any = getattr(websockets, "broadcast", None)
        if callable(ws_broadcast):
            ws_broadcast(self.clients, message)

    def on_client_message(self, callback: Callable[[str, Any], None]) -> None:
        self.message_callback = callback


__all__ = ["AsyncioWebSocketBroadcaster"]
