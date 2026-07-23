import asyncio
from typing import Optional, List
from vir_runtime.varbc.domain.action import AgentAction, ActionType
from vir_runtime.varbc.application.ports import CDPClientPort

try:
    from DrissionPage import ChromiumPage
except ImportError:
    ChromiumPage = None  # type: ignore


class DrissionAdapter(CDPClientPort):
    """DrissionPage library adapter implementing CDPClientPort for browser automation."""

    def __init__(self, addr: str = "127.0.0.1:9222") -> None:
        """Initializes DrissionAdapter with Chromium remote debugging address."""
        self._addr = addr
        self._page: Optional[object] = None
        self._console_logs: List[str] = []

    async def _ensure_page(self) -> object:
        """Helper method lazy-initializing ChromiumPage instance connected to target address."""
        if self._page is None:
            if ChromiumPage is None:
                raise ImportError("DrissionPage library is not installed.")
            self._page = ChromiumPage(addr_or_opts=self._addr)
        return self._page

    async def navigate(self, url: str) -> None:
        """Navigates ChromiumPage to the specified URL."""
        page = await self._ensure_page()
        page.get(url)  # type: ignore

    async def capture_screenshot(self, selector: str = "body") -> bytes:
        """Captures screenshot of specified selector element or page using DrissionPage."""
        page = await self._ensure_page()
        ele = page.ele(selector)  # type: ignore
        if ele:
            return ele.get_screenshot(as_bytes=True)
        return page.get_screenshot(as_bytes=True)  # type: ignore

    async def get_dom_snapshot(self) -> str:
        """Retrieves complete HTML source DOM snapshot of current page."""
        page = await self._ensure_page()
        return getattr(page, "html", "<html><body>Snapshot</body></html>")

    async def execute_action(self, action: AgentAction) -> None:
        """Executes AgentAction (CLICK, TYPE, WAIT, SCROLL) against page elements."""
        page = await self._ensure_page()
        if action.type == ActionType.CLICK and action.target:
            ele = page.ele(action.target)  # type: ignore
            if ele:
                ele.click()
        elif action.type == ActionType.TYPE and action.target:
            ele = page.ele(action.target)  # type: ignore
            if ele:
                ele.input(action.payload)
        elif action.type == ActionType.WAIT and action.payload:
            await asyncio.sleep(float(action.payload) / 1000.0)
        elif action.type == ActionType.SCROLL and action.payload:
            page.scroll.down(int(action.payload))  # type: ignore

    async def get_console_errors(self) -> List[str]:
        """Returns captured browser console error messages."""
        return list(self._console_logs)

    async def close(self) -> None:
        """Closes ChromiumPage connection and releases browser resources."""
        if self._page:
            if hasattr(self._page, "quit"):
                self._page.quit()  # type: ignore
            self._page = None
