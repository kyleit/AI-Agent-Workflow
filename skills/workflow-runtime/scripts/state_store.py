# state_store.py
import os
import json
import uuid
import tempfile
import atexit
from datetime import datetime
from typing import Any

class RevisionConflictError(Exception):
    def __init__(self, key: str, expected_revision: int, actual_revision: int):
        super().__init__(f"CAS revision conflict for '{key}': expected {expected_revision}, got {actual_revision}")
        self.key = key
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision

class StateStore:
    def get(self, key: str) -> dict:
        raise NotImplementedError

    def set(self, key: str, data: dict, expected_revision: int = None, force: bool = False) -> int:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

class NullStateStore(StateStore):
    def get(self, key: str) -> dict:
        return {}
    def set(self, key: str, data: dict, expected_revision: int = None, force: bool = False) -> int:
        return 1
    def delete(self, key: str) -> bool:
        return True

class InMemoryStateStore(StateStore):
    def __init__(self):
        self.store = {}

    def get(self, key: str) -> dict:
        return self.store.get(key, {})

    def set(self, key: str, data: dict, expected_revision: int = None, force: bool = False) -> int:
        current = self.store.get(key, {})
        current_meta = current.get("_metadata", {})
        actual_rev = current_meta.get("revision", 0)
        
        if expected_revision is not None and expected_revision != actual_rev:
            raise RevisionConflictError(key, expected_revision, actual_rev)
            
        new_data = dict(data)
        new_rev = actual_rev + 1
        new_data["_metadata"] = {
            "generation": current_meta.get("generation", 1),
            "revision": new_rev,
            "writer_id": f"{os.getpid()}-{str(uuid.uuid4())[:8]}",
            "updated_at": datetime.now().astimezone().isoformat()
        }
        self.store[key] = new_data
        return new_rev

    def delete(self, key: str) -> bool:
        if key in self.store:
            del self.store[key]
            return True
        return False

class AtomicFileStateStore(StateStore):
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self._cache = {}
        self._last_write = {}
        self._dirty = set()

    def _get_path(self, key: str) -> str:
        # Prevent directory traversal
        base = os.path.basename(key)
        if not base.endswith(".json"):
            base = base + ".json"
        return os.path.join(self.root_dir, base)

    def get(self, key: str) -> dict:
        path = self._get_path(key)
        try:
            mtime = os.path.getmtime(path)
        except Exception:
            mtime = 0
            
        if key in self._cache and self._last_write.get(key + "_mtime") == mtime:
            return self._cache[key]
            
        if not os.path.exists(path):
            self._cache[key] = {}
            self._last_write[key + "_mtime"] = 0
            return {}
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    self._cache[key] = {}
                    self._last_write[key + "_mtime"] = mtime
                    return {}
                data = json.loads(content)
                if isinstance(data, dict):
                    self._cache[key] = data
                    self._last_write[key + "_mtime"] = mtime
                    return data
        except Exception:
            pass
        return {}

    def set(self, key: str, data: dict, expected_revision: int = None, force: bool = False) -> int:
        path = self._get_path(key)
        dir_name = os.path.dirname(path)
        os.makedirs(dir_name, exist_ok=True)
        
        current = self.get(key)
        current_meta = current.get("_metadata", {})
        actual_rev = current_meta.get("revision", 0)
        
        if expected_revision is not None and expected_revision != actual_rev:
            raise RevisionConflictError(key, expected_revision, actual_rev)
            
        new_data = dict(data)
        new_rev = actual_rev + 1
        new_data["_metadata"] = {
            "generation": current_meta.get("generation", 1),
            "revision": new_rev,
            "writer_id": f"{os.getpid()}-{str(uuid.uuid4())[:8]}",
            "updated_at": datetime.now().astimezone().isoformat()
        }
        
        # Cache immediately for process-local reads
        self._cache[key] = new_data
        
        # Debounce writes for runtime & usage to reduce redundant disk updates
        should_write = True
        now = datetime.now()
        
        if not force and key in ["runtime", "usage"]:
            old_status = current.get("status")
            new_status = new_data.get("status")
            status_transitioned = old_status and new_status and old_status != new_status
            
            last_time = self._last_write.get(key)
            if last_time and (now - last_time).total_seconds() < 5.0 and not status_transitioned:
                should_write = False
                
        if should_write:
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, path)
                self._last_write[key] = now
                try:
                    self._last_write[key + "_mtime"] = os.path.getmtime(path)
                except Exception:
                    self._last_write[key + "_mtime"] = now.timestamp()
                self._dirty.discard(key)
            except Exception as e:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                raise e
        else:
            self._dirty.add(key)
            
        return new_rev

    def flush(self) -> None:
        for key in list(self._dirty):
            path = self._get_path(key)
            new_data = self._cache.get(key)
            if new_data:
                dir_name = os.path.dirname(path)
                fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, path)
                    try:
                        self._last_write[key + "_mtime"] = os.path.getmtime(path)
                    except Exception:
                        self._last_write[key + "_mtime"] = datetime.now().timestamp()
                    self._dirty.discard(key)
                except Exception:
                    if os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except Exception:
                            pass

    def delete(self, key: str) -> bool:
        path = self._get_path(key)
        if key in self._cache:
            del self._cache[key]
        if key + "_mtime" in self._last_write:
            del self._last_write[key + "_mtime"]
        self._dirty.discard(key)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except Exception:
                pass
        return False

# Global state store registry resolved based on env/mode
_store_instance = None

def get_state_store() -> StateStore:
    global _store_instance
    if _store_instance is not None:
        return _store_instance
        
    mode = os.environ.get("AIWF_RUNTIME_MODE", "normal").lower()
    disable_writes = os.environ.get("AIWF_DISABLE_STATE_WRITES", "false").lower() == "true"
    
    if disable_writes or mode == "test-memory":
        _store_instance = NullStateStore()
    elif mode == "test-isolated":
        _store_instance = InMemoryStateStore()
    else:
        root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
        _store_instance = AtomicFileStateStore(root_dir)
        
    return _store_instance

def reset_state_store(store: StateStore = None) -> None:
    global _store_instance
    _store_instance = store

def flush_stores() -> None:
    store = get_state_store()
    if hasattr(store, "flush"):
        try:
            store.flush()
        except Exception:
            pass

# Flush all changes to disk on normal exit
atexit.register(flush_stores)
