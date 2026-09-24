"""Provider configuration: project overrides, ${VAR} resolution, enable/disable.

Global config I/O (``~/.aiwf/providers.json``) and the global+project merge are
owned by :class:`KnowledgeProviderFactory`; this module layers the management
operations on top of it so there is a single source for the config path.
"""

from __future__ import annotations

import json
import os
import warnings
from typing import Any, cast

from workflow_runtime.application.knowledge.knowledge_provider_factory import \
    KnowledgeProviderFactory
from workflow_runtime.infrastructure.knowledge.provider_manager.masking import \
    mask_secrets

PROJECT_CONFIG_RELPATH: tuple[str, str] = (".agents", "memory.config.json")

get_global_config_path = KnowledgeProviderFactory.get_global_config_path
load_global_config = KnowledgeProviderFactory.load_global_config
save_global_config = KnowledgeProviderFactory.save_global_config
resolve_all_providers = KnowledgeProviderFactory.resolve_all_providers


def get_project_config_path(project_root: str = ".") -> str:
    return os.path.join(project_root or ".", *PROJECT_CONFIG_RELPATH)


def load_project_config(project_root: str = ".") -> dict[str, Any]:
    path = get_project_config_path(project_root)
    if not os.path.exists(path):
        return {"providers": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return cast(dict[str, Any], json.load(f))
    except Exception as e:
        warnings.warn(f"Failed to read project config: {e}")
        return {"providers": {}}


def resolve_env_vars(value: Any) -> Any:
    """Expand ``$VAR`` / ``${VAR}`` references in every string of a config tree."""
    if isinstance(value, str):
        return os.path.expandvars(value)
    if isinstance(value, dict):
        return {k: resolve_env_vars(v) for k, v in cast(dict[str, Any], value).items()}
    if isinstance(value, list):
        return [resolve_env_vars(v) for v in cast(list[Any], value)]
    return value


def resolve_provider_config(name: str, project_root: str = ".") -> dict[str, Any]:
    """Global config for ``name`` with project overrides applied and env vars expanded."""
    providers = cast(dict[str, Any], resolve_all_providers(project_root or ".").get("providers", {}))
    return cast(dict[str, Any], resolve_env_vars(providers.get(name, {})))


def list_providers(project_root: str = ".") -> dict[str, Any]:
    """All merged providers with env vars expanded and secrets masked."""
    providers = resolve_all_providers(project_root or ".").get("providers", {})
    return cast(dict[str, Any], mask_secrets(resolve_env_vars(providers)))


def _set_enabled(name: str, enabled: bool) -> bool:
    config = load_global_config()
    providers = cast(dict[str, Any], config.setdefault("providers", {}))
    cast(dict[str, Any], providers.setdefault(name, {}))["enabled"] = enabled
    return save_global_config(config)


def enable_provider(name: str) -> bool:
    return _set_enabled(name, True)


def disable_provider(name: str) -> bool:
    return _set_enabled(name, False)


__all__ = [
    "disable_provider",
    "enable_provider",
    "get_global_config_path",
    "get_project_config_path",
    "list_providers",
    "load_global_config",
    "load_project_config",
    "resolve_all_providers",
    "resolve_env_vars",
    "resolve_provider_config",
    "save_global_config",
]
