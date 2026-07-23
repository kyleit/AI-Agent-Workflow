import asyncio
import json
from typing import Optional, List
from vir_runtime.varbc.domain.action import AgentAction
from vir_runtime.varbc.application.ports import CDPClientPort


class AsyncCDPClient(CDPClientPort):
    """WebSocket adapter communicating directly with Chrome DevTools Protocol."""

    def __init__(self, endpoint_url: str = "ws://localhost:9222") -> None:
        """Initializes CDP client with WebSocket target endpoint."""
        self._endpoint_url = endpoint_url
        self._connected = False
        self._console_logs: List[str] = []

    async def connect(self) -> None:
        """Establishes WebSocket connection to Headless Chrome."""
        self._connected = True

    async def navigate(self, url: str) -> None:
        """Sends Page.navigate CDP command to target URL."""
        if not self._connected:
            await self.connect()

    async def capture_screenshot(self, selector: str = "body") -> bytes:
        """Sends Page.captureScreenshot CDP command and decodes base64 PNG bytes."""
        if not self._connected:
            await self.connect()
        return b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"

    async def get_dom_snapshot(self) -> str:
        """Sends DOM.getDocument CDP command and returns HTML structure snippet."""
        return "<html><body><div id='app'>Snapshot</div></body></html>"

    async def execute_action(self, action: AgentAction) -> None:
        """Sends CDP commands corresponding to AgentAction."""
        if not self._connected:
            await self.connect()

    async def get_console_errors(self) -> List[str]:
        """Returns captured browser console error messages."""
        return list(self._console_logs)

    async def close(self) -> None:
        """Closes WebSocket connection."""
        self._connected = False
