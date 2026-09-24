"""Knowledge provider management (``aiwf provider``): config, secrets, health, Obsidian.

Restores the behaviour of the retired ``knowledge_runtime.provider_manager``
(c6df50ce) on top of :class:`KnowledgeProviderFactory`.
"""

from __future__ import annotations

from workflow_runtime.infrastructure.knowledge.provider_manager.config import (
    disable_provider, enable_provider, get_global_config_path,
    get_project_config_path, list_providers, load_global_config,
    load_project_config, resolve_all_providers, resolve_env_vars,
    resolve_provider_config, save_global_config)
from workflow_runtime.infrastructure.knowledge.provider_manager.health import \
    test_provider
from workflow_runtime.infrastructure.knowledge.provider_manager.masking import \
    mask_secrets
from workflow_runtime.infrastructure.knowledge.provider_manager.obsidian_folder import (
    make_project_slug, resolve_obsidian_project_folder, resolve_project_id)
from workflow_runtime.infrastructure.knowledge.provider_manager.obsidian_sync import \
    sync_obsidian

__all__ = [
    "disable_provider",
    "enable_provider",
    "get_global_config_path",
    "get_project_config_path",
    "list_providers",
    "load_global_config",
    "load_project_config",
    "make_project_slug",
    "mask_secrets",
    "resolve_all_providers",
    "resolve_env_vars",
    "resolve_obsidian_project_folder",
    "resolve_project_id",
    "resolve_provider_config",
    "save_global_config",
    "sync_obsidian",
    "test_provider",
]
