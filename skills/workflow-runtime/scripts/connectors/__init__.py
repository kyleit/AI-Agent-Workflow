# connectors/__init__.py
# ConnectorRegistry — discovers, registers, and routes provider connector calls.
from __future__ import annotations

import importlib
import json
import os
import sys
from typing import Dict, List, Optional

from connectors.base import (
    DetectedProvider,
    DiagnosticsResult,
    NormalizedUsageRecord,
    ProviderConnector,
)

# Path to connectors.json manifest (same data/ directory as pricing.json)
_MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "connectors.json"
)


class ConnectorRegistry:
    """
    Registry and router for all provider connectors.

    Usage:
        registry = build_default_registry()
        providers = registry.detect_all()
        records = registry.parse("antigravity", conv_id)
    """

    def __init__(self):
        self._connectors: Dict[str, ProviderConnector] = {}

    def register(self, connector: ProviderConnector) -> None:
        """Register a connector instance by its canonical provider name."""
        name = connector.get_provider_name()
        self._connectors[name] = connector

    def get_connector(self, provider_name: str) -> Optional[ProviderConnector]:
        """Return a registered connector by name, or None."""
        return self._connectors.get(provider_name)

    def detect_all(self) -> List[DetectedProvider]:
        """
        Run detect() on all registered connectors.

        Returns:
            List of DetectedProvider (includes only non-None results).
        """
        results = []
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

    def parse(self, provider_name: str, conv_id: str) -> List[NormalizedUsageRecord]:
        """
        Parse usage data for a given provider and conversation.

        Args:
            provider_name: Canonical provider name (must be registered).
            conv_id: Conversation ID to parse.

        Returns:
            List of NormalizedUsageRecord. Empty list if not found.

        Raises:
            ConnectorNotFoundError if provider_name not registered.
        """
        connector = self._connectors.get(provider_name)
        if connector is None:
            raise ConnectorNotFoundError(provider_name, list(self._connectors.keys()))
        try:
            return connector.parse_conversation(conv_id)
        except Exception:
            return []

    def diagnose_all(self) -> List[DiagnosticsResult]:
        """
        Run get_diagnostics() on all registered connectors.

        Returns:
            List of DiagnosticsResult (one per registered connector).
        """
        results = []
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

    def _load_manifest(self) -> list:
        """Load and parse connectors.json manifest."""
        manifest_path = os.path.abspath(_MANIFEST_PATH)
        if not os.path.exists(manifest_path):
            return []
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("connectors", [])
        except (json.JSONDecodeError, IOError):
            return []

    def list_registered(self) -> List[str]:
        """Return list of registered provider names."""
        return list(self._connectors.keys())


class ConnectorNotFoundError(Exception):
    """Raised when a requested provider connector is not registered."""

    def __init__(self, provider_name: str, registered: List[str]):
        self.provider_name = provider_name
        self.registered = registered
        super().__init__(
            f"Connector '{provider_name}' not found. "
            f"Registered providers: {registered}"
        )


class TranscriptNotFoundError(Exception):
    """Raised when a transcript file cannot be located for a conversation."""

    def __init__(self, conv_id: str, path: str = ""):
        self.conv_id = conv_id
        self.path = path
        super().__init__(
            f"Transcript not found for conversation '{conv_id}'"
            + (f" at path: {path}" if path else "")
        )


def build_default_registry() -> ConnectorRegistry:
    """
    Factory function: create a ConnectorRegistry pre-populated with all
    enabled connectors from the connectors.json manifest.

    Uses importlib dynamic loading so new connectors require no code changes
    to this file — only a connectors.json entry.

    Returns:
        ConnectorRegistry with all enabled connectors registered.
    """
    registry = ConnectorRegistry()
    manifest_path = os.path.abspath(_MANIFEST_PATH)

    if not os.path.exists(manifest_path):
        # Manifest missing — register connectors directly as fallback
        _register_fallback(registry)
        return registry

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("connectors", [])
    except (json.JSONDecodeError, IOError):
        _register_fallback(registry)
        return registry

    for entry in entries:
        if not entry.get("enabled", True):
            continue
        module_path = entry.get("module", "")
        class_name = entry.get("class", "")
        if not module_path or not class_name:
            continue
        try:
            # Ensure connectors/ directory is importable
            scripts_dir = os.path.dirname(os.path.dirname(__file__))
            if scripts_dir not in sys.path:
                sys.path.insert(0, scripts_dir)
            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)
            registry.register(cls())
        except Exception:
            # Silently skip connectors that fail to load — log to diagnostics at runtime
            pass

    return registry


def _register_fallback(registry: ConnectorRegistry) -> None:
    """Fallback: register connectors directly when manifest is unavailable."""
    try:
        from connectors.antigravity import AntigravityConnector
        registry.register(AntigravityConnector())
    except ImportError:
        pass
    try:
        from connectors.claude_code import ClaudeCodeConnector
        registry.register(ClaudeCodeConnector())
    except ImportError:
        pass
    try:
        from connectors.cursor import CursorConnector
        registry.register(CursorConnector())
    except ImportError:
        pass
    try:
        from connectors.vscode_agents import VSCodeAgentsConnector
        registry.register(VSCodeAgentsConnector())
    except ImportError:
        pass
