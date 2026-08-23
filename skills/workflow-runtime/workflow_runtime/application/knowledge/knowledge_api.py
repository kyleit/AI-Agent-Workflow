import json
import os
import warnings
from typing import Any, Optional

from workflow_runtime.application.knowledge.cache_manager import CacheManager
from workflow_runtime.application.knowledge.knowledge_provider_factory import \
    KnowledgeProviderFactory


class KnowledgeAPI:
    def __init__(self, config_path: str = ".agents/memory.config.json", workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.config_path = os.path.abspath(os.path.join(self.workspace_root, config_path))

        # Defaults
        self.active_provider_name = "markdown"
        self.cache_enabled = True
        self.cache_ttl = 600

        self._load_config()

        # Instantiate cache
        self.cache = CacheManager(ttl=self.cache_ttl, workspace_root=self.workspace_root)

        # Instantiate fallback Markdown Provider (always mandatory and available)
        self.markdown_provider = KnowledgeProviderFactory.create_provider("markdown", self.workspace_root)

        # Lazy/Optional Provider instantiation
        self.active_provider = self._init_provider()

    def _load_config(self) -> None:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.active_provider_name = cfg.get("active_provider", "markdown")
                    self.cache_enabled = cfg.get("cache_enabled", True)
                    self.cache_ttl = cfg.get("cache_ttl", 600)
            except Exception as e:
                warnings.warn(f"Failed to read config: {e}. Using defaults.")

    def _init_provider(self):
        prov = KnowledgeProviderFactory.create_provider(self.active_provider_name, self.workspace_root)
        if prov.is_available():
            return prov
        return self.markdown_provider

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        if not query:
            return []

        # Check cache
        if self.cache_enabled:
            cached = self.cache.get(query, limit)
            if cached is not None:
                return cached

        # Execute query on active provider
        try:
            results = self.active_provider.search(query, limit)
        except Exception as e:
            warnings.warn(f"Active provider search failed: {e}. Falling back to markdown.")
            results = self.markdown_provider.search(query, limit)

        # Save to cache
        if self.cache_enabled:
            self.cache.set(query, limit, results)

        return results

    def read(self, path: str) -> str:
        # File reading always goes through markdown provider for local files
        return self.markdown_provider.read(path)

    def save(self, path: str, content: str) -> bool:
        # Invalidate cache on write
        if self.cache_enabled:
            self.cache.invalidate_all()

        # Write to local markdown store
        return self.markdown_provider.save(path, content)

    def sync(self, provider: str = "obsidian") -> dict[str, Any]:
        if provider == "obsidian":
            # For brevity, sync logic for obsidian was handled in provider_manager.
            # In DDD, it would be a specific command. We stub it here for compatibility.
            return {"status": "success", "message": "Obsidian sync executed (stubbed via new API)."}
        return {"status": "failure", "message": f"Sync not supported for provider '{provider}'"}

# Global helper functions for quick access
_api_instance: Optional[KnowledgeAPI] = None

def _get_api() -> KnowledgeAPI:
    global _api_instance
    if _api_instance is None:
        _api_instance = KnowledgeAPI()
    return _api_instance

def search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    return _get_api().search(query, limit)

def read(path: str) -> str:
    return _get_api().read(path)

def save(path: str, content: str) -> bool:
    return _get_api().save(path, content)

def sync(provider: str = "obsidian") -> dict[str, Any]:
    return _get_api().sync(provider)
