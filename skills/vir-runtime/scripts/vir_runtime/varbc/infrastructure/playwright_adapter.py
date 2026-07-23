import asyncio
from typing import Optional, List
from vir_runtime.varbc.domain.action import AgentAction, ActionType
from vir_runtime.varbc.application.ports import CDPClientPort

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None  # type: ignore


class PlaywrightAdapter(CDPClientPort):
    """Playwright async API adapter implementing CDPClientPort."""

    def __init__(self, browser_ws_endpoint: Optional[str] = None) -> None:
        """Initializes PlaywrightAdapter with optional browser WebSocket endpoint."""
        self._ws_endpoint = browser_ws_endpoint
        self._playwright: Optional[object] = None
        self._browser: Optional[object] = None
        self._page: Optional[object] = None
        self._console_logs: List[str] = []

    async def _ensure_page(self) -> object:
        """Helper method lazy-initializing Playwright instance, browser, and page."""
        if self._page is None:
            if async_playwright is None:
                raise ImportError("Playwright library is not installed.")
            self._playwright = await async_playwright().start()
            if self._ws_endpoint:
                self._browser = await self._playwright.chromium.connect_over_cdp(self._ws_endpoint)  # type: ignore
            else:
                self._browser = await self._playwright.chromium.launch(headless=True)  # type: ignore
            self._page = await self._browser.new_page()  # type: ignore
        return self._page

    async def navigate(self, url: str) -> None:
        """Navigates Playwright page to specified target URL."""
        page = await self._ensure_page()
        await page.goto(url, wait_until="networkidle")  # type: ignore

    async def capture_screenshot(self, selector: str = "body") -> bytes:
        """Captures screenshot of specified selector element or page using Playwright."""
        page = await self._ensure_page()
        locator = page.locator(selector)  # type: ignore
        if await locator.count() > 0:
            return await locator.screenshot(type="png")
        return await page.screenshot(type="png")  # type: ignore

    async def get_dom_snapshot(self) -> str:
        """Retrieves DOM HTML snapshot using Playwright page.content()."""
        page = await self._ensure_page()
        return await page.content()  # type: ignore

    async def execute_action(self, action: AgentAction) -> None:
        """Executes AgentAction (CLICK, TYPE, WAIT, SCROLL) against page elements."""
        page = await self._ensure_page()
        if action.type == ActionType.CLICK and action.target:
            await page.click(action.target)  # type: ignore
        elif action.type == ActionType.TYPE and action.target:
            await page.fill(action.target, action.payload)  # type: ignore
        elif action.type == ActionType.WAIT and action.payload:
            await asyncio.sleep(float(action.payload) / 1000.0)
        elif action.type == ActionType.SCROLL and action.payload:
            await page.evaluate(f"window.scrollBy(0, {action.payload})")  # type: ignore

    async def get_console_errors(self) -> List[str]:
        """Returns captured browser console error messages."""
        return list(self._console_logs)

    async def close(self) -> None:
        """Closes Playwright browser session and stops Playwright context."""
        if self._browser:
            await self._browser.close()  # type: ignore
            self._browser = None
        if self._playwright:
            await self._playwright.stop()  # type: ignore
            self._playwright = None
        self._page = None
