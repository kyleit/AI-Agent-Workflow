from __future__ import annotations

import asyncio
from typing import Any

from workflow_runtime.application.visual.varbc.ports import CDPClientPort
from workflow_runtime.domain.visual.varbc.action import ActionType, AgentAction

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright: Any = None


class PlaywrightAdapter(CDPClientPort):
    """Playwright async API adapter implementing CDPClientPort."""

    def __init__(self, browser_ws_endpoint: str | None = None) -> None:
        """Initializes PlaywrightAdapter with optional browser WebSocket endpoint."""
        self._ws_endpoint = browser_ws_endpoint
        self._playwright: Any = None
        self._browser: Any = None
        self._page: Any = None
        self._console_logs: list[str] = []

    async def _ensure_page(self) -> Any:
        """Helper method lazy-initializing Playwright instance, browser, and page."""
        if self._page is None:
            if async_playwright is None:
                raise ImportError("Playwright library is not installed.")
            self._playwright = await async_playwright().start()
            if self._ws_endpoint:
                self._browser = await getattr(self._playwright, "chromium").connect_over_cdp(self._ws_endpoint)
            else:
                self._browser = await getattr(self._playwright, "chromium").launch(headless=True)
            self._page = await getattr(self._browser, "new_page")()
        return self._page

    async def navigate(self, url: str) -> None:
        """Navigates Playwright page to specified target URL."""
        page = await self._ensure_page()
        await getattr(page, "goto")(url, wait_until="networkidle")

    async def capture_screenshot(self, selector: str = "body") -> bytes:
        """Captures screenshot of specified selector element or page using Playwright."""
        page = await self._ensure_page()
        locator = getattr(page, "locator")(selector)
        if await getattr(locator, "count")() > 0:
            return bytes(await getattr(locator, "screenshot")(type="png"))
        return bytes(await getattr(page, "screenshot")(type="png"))

    async def get_dom_snapshot(self) -> str:
        """Retrieves DOM HTML snapshot using Playwright page.content()."""
        page = await self._ensure_page()
        return str(await getattr(page, "content")())

    async def execute_action(self, action: AgentAction) -> None:
        """Executes AgentAction (CLICK, TYPE, WAIT, SCROLL) against page elements."""
        page = await self._ensure_page()
        if action.type == ActionType.CLICK and action.target:
            await getattr(page, "click")(action.target)
        elif action.type == ActionType.TYPE and action.target:
            await getattr(page, "fill")(action.target, str(action.payload))
        elif action.type == ActionType.WAIT and action.payload:
            await asyncio.sleep(float(action.payload) / 1000.0)
        elif action.type == ActionType.SCROLL and action.payload:
            await getattr(page, "evaluate")(f"window.scrollBy(0, {action.payload})")

    async def get_console_errors(self) -> list[str]:
        """Returns captured browser console error messages."""
        return list(self._console_logs)

    async def close(self) -> None:
        """Closes Playwright browser session and stops Playwright context."""
        if self._browser:
            await getattr(self._browser, "close")()
            self._browser = None
        if self._playwright:
            await getattr(self._playwright, "stop")()
            self._playwright = None
        self._page = None


__all__ = ["PlaywrightAdapter"]
