# File path: vir_runtime/adapters/base.py
from typing import Protocol

class BrowserAdapter(Protocol):
    def open(self, url: str) -> None:
        """Navigate to the target URL."""
        ...

    def capture_screenshot(self, path: str) -> None:
        """Capture browser screenshot and save to path."""
        ...

    def get_dom_content(self) -> str:
        """Query and return the current layout DOM content string."""
        ...

    def close(self) -> None:
        """Close browser instance and clean connections."""
        ...
