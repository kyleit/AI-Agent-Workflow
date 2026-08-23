from __future__ import annotations

from typing import Any

from workflow_runtime.application.workflow import aiwf_registry

"""
infrastructure/registry/registry_adapter.py

DDD Adapter wrapping aiwf_registry.py.
Manages the global project registry (~/.aiwf/registry.json).
"""


class RegistryAdapter:
    """DDD Adapter for the global AIWF project registry.

    Wraps aiwf_registry.py with a clean interface.
    """

    def __init__(self) -> None:
        pass

    def load(self) -> dict[str, Any]:
        """Load and return the full registry dict."""
        return aiwf_registry.load_registry()

    def list_projects(self) -> list[dict[str, Any]]:
        """Return list of all registered project dicts."""
        return aiwf_registry.list_projects()

    def register(self, project_path: str, force: bool = False,
                 source: str = "register", framework_root: str | None = None) -> dict[str, Any]:
        """Register a project in the global registry. Returns project entry."""
        return aiwf_registry.register_project(
            project_path, force=force, source=source, framework_root=framework_root
        )

    def unregister(self, project_path: str) -> bool:
        """Remove a project from the registry."""
        return aiwf_registry.unregister_project(project_path)

    def update_telegram_chat_id(self, project_path: str, chat_id: str) -> bool:
        """Update the Telegram chat_id for a registered project."""
        return aiwf_registry.update_project_telegram_chat_id(project_path, chat_id)

    def find_by_path(self, project_path: str) -> dict[str, Any] | None:
        """Find a project entry by exact or canonical path."""
        norm_target = str(aiwf_registry.normalize_path(project_path))
        for p in aiwf_registry.list_projects():
            if str(aiwf_registry.normalize_path(str(p.get("path", "")))) == norm_target:
                return p
        return None

    def is_registered(self, project_path: str) -> bool:
        """Return True if path is in registry."""
        return self.find_by_path(project_path) is not None


__all__ = ["RegistryAdapter"]
