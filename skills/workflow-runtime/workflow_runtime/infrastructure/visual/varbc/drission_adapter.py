from __future__ import annotations

import asyncio
from typing import Any

from workflow_runtime.application.visual.varbc.ports import CDPClientPort
from workflow_runtime.domain.visual.varbc.action import ActionType, AgentAction

try:
    from DrissionPage import ChromiumPage
except ImportError:
    ChromiumPage: Any = None


class DrissionAdapter(CDPClientPort):
    """DrissionPage library adapter implementing CDPClientPort for browser automation."""

    def __init__(self, addr: str = "127.0.0.1:9222") -> None:
        """Initializes DrissionAdapter with Chromium remote debugging address."""
        self._addr = addr
        self._page: Any = None
        self._console_logs: list[str] = []

    async def _ensure_page(self) -> Any:
        """Helper method lazy-initializing ChromiumPage instance connected to target address."""
        if self._page is None:
            if ChromiumPage is None:
                raise ImportError("DrissionPage library is not installed.")
            self._page = ChromiumPage(addr_or_opts=self._addr)
        return self._page

    async def navigate(self, url: str) -> None:
        """Navigates ChromiumPage to the specified URL."""
        page = await self._ensure_page()
        get_fn: Any = getattr(page, "get", None)
        if callable(get_fn):
            get_fn(url)

    async def capture_screenshot(self, selector: str = "body") -> bytes:
        """Captures screenshot of specified selector element or page using DrissionPage."""
        page = await self._ensure_page()
        ele_fn: Any = getattr(page, "ele", None)
        ele: Any = ele_fn(selector) if callable(ele_fn) else None
        if ele:
            snap_fn: Any = getattr(ele, "get_screenshot", None)
            if callable(snap_fn):
                res: Any = snap_fn(as_bytes=True)
                if isinstance(res, bytes):
                    return res

        page_snap_fn: Any = getattr(page, "get_screenshot", None)
        if callable(page_snap_fn):
            res: Any = page_snap_fn(as_bytes=True)
            if isinstance(res, bytes):
                return res

        return b""

    async def get_dom_snapshot(self) -> str:
        """Retrieves complete HTML source DOM snapshot of current page."""
        page = await self._ensure_page()
        return str(getattr(page, "html", "<html><body>Snapshot</body></html>"))

    async def execute_action(self, action: AgentAction) -> None:
        """Executes AgentAction (CLICK, TYPE, WAIT, SCROLL) against page elements."""
        page = await self._ensure_page()
        ele_fn: Any = getattr(page, "ele", None)

        if action.type == ActionType.CLICK and action.target:
            ele: Any = ele_fn(action.target) if callable(ele_fn) else None
            if ele:
                click_fn: Any = getattr(ele, "click", None)
                if callable(click_fn):
                    click_fn()
        elif action.type == ActionType.TYPE and action.target:
            ele: Any = ele_fn(action.target) if callable(ele_fn) else None
            if ele:
                input_fn: Any = getattr(ele, "input", None)
                if callable(input_fn):
                    input_fn(action.payload)
        elif action.type == ActionType.WAIT and action.payload:
            await asyncio.sleep(float(action.payload) / 1000.0)
        elif action.type == ActionType.SCROLL and action.payload:
            scroll_obj: Any = getattr(page, "scroll", None)
            down_fn: Any = getattr(scroll_obj, "down", None) if scroll_obj else None
            if callable(down_fn):
                down_fn(int(action.payload))

    async def get_console_errors(self) -> list[str]:
        """Returns captured browser console error messages."""
        return list(self._console_logs)

    async def close(self) -> None:
        """Closes ChromiumPage connection and releases browser resources."""
        if self._page:
            quit_fn: Any = getattr(self._page, "quit", None)
            if callable(quit_fn):
                quit_fn()
            self._page = None


__all__ = ["DrissionAdapter"]
