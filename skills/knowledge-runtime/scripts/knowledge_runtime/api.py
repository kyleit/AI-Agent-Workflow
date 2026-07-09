import os
import json
import warnings
from .providers.markdown import MarkdownProvider
from .providers.sqlite import SQLiteProvider
from .providers.vector import VectorDBProvider
from .providers.obsidian import ObsidianProvider
from .cache import CacheManager

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
        self.markdown_provider = MarkdownProvider(workspace_root=self.workspace_root)
        
        # Lazy/Optional Provider instantiation
        self.active_provider = self._init_provider()

    def _load_config(self):
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
        if self.active_provider_name == "sqlite":
            prov = SQLiteProvider(workspace_root=self.workspace_root)
            if prov.is_available():
                return prov
        elif self.active_provider_name == "vector_db":
            prov = VectorDBProvider()
            if prov.is_available():
                return prov
        elif self.active_provider_name == "obsidian":
            prov = ObsidianProvider()
            if prov.is_available():
                return prov
        
        # Default or fallback to markdown
        return self.markdown_provider

    def search(self, query: str, limit: int = 5) -> list[dict]:
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


# Global helper functions for quick access
_api_instance = None

def _get_api():
    global _api_instance
    if _api_instance is None:
        _api_instance = KnowledgeAPI()
    return _api_instance

def search(query: str, limit: int = 5) -> list[dict]:
    return _get_api().search(query, limit)

def read(path: str) -> str:
    return _get_api().read(path)

def save(path: str, content: str) -> bool:
    return _get_api().save(path, content)
