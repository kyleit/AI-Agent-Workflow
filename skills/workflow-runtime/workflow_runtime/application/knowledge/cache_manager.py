import hashlib
import json
import os
import time
from typing import Any, Optional


class CacheManager:
    def __init__(self, cache_file: str = ".agents/state/knowledge_cache.json", ttl: int = 600, workspace_root: str = "."):
        self.workspace_root = os.path.abspath(workspace_root)
        self.cache_file = os.path.abspath(os.path.join(self.workspace_root, cache_file))
        self.ttl = ttl
        self._cache: dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, indent=2)
        except Exception:
            pass

    def _get_hash(self, query: str, limit: int) -> str:
        data = f"{query}_{limit}"
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def get(self, query: str, limit: int = 5) -> Optional[list[dict[str, Any]]]:
        key = self._get_hash(query, limit)
        entry = self._cache.get(key)
        if entry:
            if time.time() < entry.get("expires_at", 0):
                return entry.get("value")
            else:
                # Remove expired entry
                self._cache.pop(key, None)
                self._save_cache()
        return None

    def set(self, query: str, limit: int, value: list[dict[str, Any]]) -> None:
        key = self._get_hash(query, limit)
        self._cache[key] = {
            "value": value,
            "expires_at": int(time.time() + self.ttl)
        }
        self._save_cache()

    def invalidate_all(self) -> None:
        self._cache = {}
        self._save_cache()
