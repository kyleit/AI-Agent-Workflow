# File path: vir_runtime/adapters/registry.py
from __future__ import annotations

import os
from typing import Any, cast

import yaml


class MockBrowserAdapter:
    def __init__(self) -> None:
        self.url = ""
        self.closed = False

    def open(self, url: str) -> None:
        self.url = url
        print(f"[MockBrowserAdapter] Opened URL: {url}")

    def capture_screenshot(self, path: str) -> None:
        print(f"[MockBrowserAdapter] Captured screenshot to: {path}")
        with open(path, "wb") as f:
            f.write(b"mock_png_data")

    def get_dom_content(self) -> str:
        return "<html><body>Mock DOM</body></html>"

    def close(self) -> None:
        self.closed = True
        print("[MockBrowserAdapter] Closed browser.")


class AdapterRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, type[Any]] = {
            "mock": MockBrowserAdapter
        }
        self._instances: dict[str, Any] = {}

    def register_adapter(self, name: str, adapter_cls: type[Any]) -> None:
        """Register an adapter class under a unique name."""
        self._registry[name] = adapter_cls

    def get_adapter(self, name: str) -> Any:
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
                raw_config = yaml.safe_load(f)
            config = cast(dict[str, Any], raw_config) if isinstance(raw_config, dict) else {}
            vir_dict = cast(dict[str, Any], config.get("vir")) if isinstance(config.get("vir"), dict) else {}
            provider = str(vir_dict.get("provider", "mock") or "mock")
            if provider in self._registry:
                self.get_adapter(provider)


__all__ = [
    "MockBrowserAdapter",
    "AdapterRegistry",
]
