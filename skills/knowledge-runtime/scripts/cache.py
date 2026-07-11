# cache.py
import time
import hashlib
from knowledge_runtime.cache import CacheManager

class RuntimeCache:
    def __init__(self, db_path: str = ".agents/state/knowledge_cache.json", ttl_seconds: int = 600):
        self.manager = CacheManager(cache_file=db_path, ttl=ttl_seconds)

    def _get_hash(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict:
        h = self._get_hash(key)
        entry = self.manager._cache.get(h)
        if entry:
            if time.time() < entry.get("expires_at", 0):
                return entry.get("value")
            else:
                self.manager._cache.pop(h, None)
                self.manager._save_cache()
        return None

    def set(self, key: str, value: dict) -> None:
        h = self._get_hash(key)
        self.manager._cache[h] = {
            "value": value,
            "expires_at": int(time.time() + self.manager.ttl)
        }
        self.manager._save_cache()

    def invalidate(self, key: str) -> None:
        h = self._get_hash(key)
        self.manager._cache.pop(h, None)
        self.manager._save_cache()

    def clear(self) -> None:
        self.manager.invalidate_all()
