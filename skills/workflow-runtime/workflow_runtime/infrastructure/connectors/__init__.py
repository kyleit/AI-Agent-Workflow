# connectors/__init__.py
# ConnectorRegistry — discovers, registers, and routes provider connector calls.
from __future__ import annotations

import importlib
import json
import os
from typing import Any, cast

from workflow_runtime.infrastructure.connectors.base import (
    DetectedProvider, DiagnosticsResult, NormalizedUsageRecord,
    ProviderConnector)

_MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "connectors.json"
)


class ConnectorNotFoundError(Exception):
    def __init__(self, provider_name: str, registered: list[str]) -> None:
        super().__init__(f"Connector for '{provider_name}' not registered. Registered: {registered}")
        self.provider_name = provider_name
        self.registered = registered


class ConnectorRegistry:
    """
    Registry and router for all provider connectors.
    """

    def __init__(self) -> None:
        self._connectors: dict[str, ProviderConnector] = {}

    def register(self, connector: ProviderConnector) -> None:
        """Register a connector instance by its canonical provider name."""
        name = connector.get_provider_name()
        self._connectors[name] = connector

    def get_connector(self, provider_name: str) -> ProviderConnector | None:
        """Return a registered connector by name, or None."""
        return self._connectors.get(provider_name)

    def detect_all(self) -> list[DetectedProvider]:
        """
        Run detect() on all registered connectors.
        """
        results: list[DetectedProvider] = []
        for name, connector in self._connectors.items():
            try:
                result = connector.detect()
                if result is not None:
                    results.append(result)
                else:
                    results.append(DetectedProvider(
                        provider_name=name,
                        path="",
                        version="",
                        status="not_found",
                    ))
            except Exception as exc:
                results.append(DetectedProvider(
                    provider_name=name,
                    path="",
                    version="",
                    status="error",
                    error=str(exc),
                ))
        return results

    def parse(self, provider_name: str, conv_id: str) -> list[NormalizedUsageRecord]:
        """
        Parse usage data for a given provider and conversation.
        """
        connector = self._connectors.get(provider_name)
        if connector is None:
            raise ConnectorNotFoundError(provider_name, list(self._connectors.keys()))
        try:
            return connector.parse_conversation(conv_id)
        except Exception:
            return []

    def diagnose_all(self) -> list[DiagnosticsResult]:
        """
        Run get_diagnostics() on all registered connectors.
        """
        results: list[DiagnosticsResult] = []
        for name, connector in self._connectors.items():
            try:
                results.append(connector.get_diagnostics())
            except Exception as exc:
                results.append(DiagnosticsResult(
                    provider_name=name,
                    status="error",
                    error_message=str(exc),
                    accuracy_confidence="unknown",
                ))
        return results

    def _load_manifest(self) -> list[dict[str, Any]]:
        """Load and parse connectors.json manifest."""
        manifest_path = os.path.abspath(_MANIFEST_PATH)
        if not os.path.exists(manifest_path):
            return []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return cast(list[dict[str, Any]], data)
                elif isinstance(data, dict):
                    data_dict = cast(dict[str, Any], data)
                    raw = data_dict.get("connectors", [])
                    return cast(list[dict[str, Any]], raw) if isinstance(raw, list) else []
                return []
        except Exception:
            return []

    def auto_discover(self) -> None:
        """Auto-discover and instantiate connectors defined in connectors.json."""
        manifest = self._load_manifest()
        for entry in manifest:
            module_name = entry.get("module")
            class_name = entry.get("class")
            enabled = entry.get("enabled", True)
            if not enabled or not module_name or not class_name:
                continue

            try:
                mod = importlib.import_module(str(module_name))
                cls = getattr(mod, str(class_name), None)
                if cls is not None and callable(cls):
                    inst = cls()
                    if isinstance(inst, ProviderConnector):
                        self.register(inst)
            except Exception:
                pass


def build_default_registry() -> ConnectorRegistry:
    """Factory: creates a ConnectorRegistry and runs auto_discover()."""
    registry = ConnectorRegistry()
    registry.auto_discover()
    return registry


__all__ = [
    "ConnectorNotFoundError",
    "ConnectorRegistry",
    "build_default_registry",
]
