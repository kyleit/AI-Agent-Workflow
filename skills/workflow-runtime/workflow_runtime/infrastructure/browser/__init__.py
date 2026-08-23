"""CDP browser infrastructure adapter package."""

from workflow_runtime.infrastructure.browser.cdp_client import CDPClient
from workflow_runtime.infrastructure.browser.cdp_session import CDPSession
from workflow_runtime.infrastructure.browser.dom_inspector import DOMInspector
from workflow_runtime.infrastructure.browser.screenshot_capturer import \
    ScreenshotCapturer

__all__ = [
    "CDPClient",
    "CDPSession",
    "DOMInspector",
    "ScreenshotCapturer",
]
