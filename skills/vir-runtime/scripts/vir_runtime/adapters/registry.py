# File path: vir_runtime/adapters/registry.py
import yaml
import os
from typing import Dict, Type, Any
from vir_runtime.adapters.base import BrowserAdapter

class MockBrowserAdapter:
    def __init__(self):
        self.url = ""
        self.closed = False

    def open(self, url: str) -> None:
        self.url = url
        print(f"[MockBrowserAdapter] Opened URL: {url}")

    def capture_screenshot(self, path: str) -> None:
        print(f"[MockBrowserAdapter] Captured screenshot to: {path}")
        # Create an empty file to mock screenshot capture
        with open(path, "wb") as f:
            f.write(b"mock_png_data")

    def get_dom_content(self) -> str:
        return "<html><body>Mock DOM</body></html>"

    def close(self) -> None:
        self.closed = True
        print("[MockBrowserAdapter] Closed browser.")


class AdapterRegistry:
    def __init__(self):
        self._registry: Dict[str, Type[BrowserAdapter]] = {
            "mock": MockBrowserAdapter
        }
        self._instances: Dict[str, BrowserAdapter] = {}

    def register_adapter(self, name: str, adapter_cls: Type[BrowserAdapter]) -> None:
        """Register an adapter class under a unique name."""
        self._registry[name] = adapter_cls

    def get_adapter(self, name: str) -> BrowserAdapter:
        """Get or initialize the adapter instance by name."""
        if name not in self._instances:
            if name not in self._registry:
                raise ValueError(f"Adapter '{name}' is not registered in the Registry.")
            self._instances[name] = self._registry[name]()
        return self._instances[name]

    def load_from_config(self, config_path: str = "config.yaml") -> None:
        """Dynamically load configured default provider adapter."""
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            provider = config.get("vir", {}).get("provider", "mock")
            # If default provider is registered, pre-initialize it
            if provider in self._registry:
                self.get_adapter(provider)
