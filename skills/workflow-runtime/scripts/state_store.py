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
        
        scoped_keys = [
            "workflow", "tasks", "agents", "locks", "handoffs", 
            "checkpoints", "timeline", "authorization", "approvals", "usage"
        ]
        if key in scoped_keys:
            work_item_id = get_active_work_item_id()
            if work_item_id:
                return os.path.join(self.root_dir, "work-items", work_item_id, base)
                
        return os.path.join(self.root_dir, base)

    def get(self, key: str) -> dict:
        path = self._get_path(key)
        
        scoped_keys = [
            "workflow", "tasks", "agents", "locks", "handoffs", 
            "checkpoints", "timeline", "authorization", "approvals", "usage"
        ]
        if key in scoped_keys:
            work_item_id = get_active_work_item_id()
            if work_item_id and not os.path.exists(path):
                legacy_path = os.path.join(self.root_dir, os.path.basename(path))
                if os.path.exists(legacy_path):
                    try:
                        with open(legacy_path, "r", encoding="utf-8") as f:
                            legacy_data = json.load(f)
                        
                        # Only migrate if the legacy state belongs to this work item
                        legacy_id = None
                        if isinstance(legacy_data, dict):
                            legacy_id = legacy_data.get("work_item", {}).get("id") or legacy_data.get("work_item_id")
                        
                        if not legacy_id or legacy_id == work_item_id:
                            # Scope it
                            os.makedirs(os.path.dirname(path), exist_ok=True)
                            with open(path, "w", encoding="utf-8") as f:
                                json.dump(legacy_data, f, indent=2, ensure_ascii=False)
                            
                            # Cache immediately
                            self._cache[key] = legacy_data
                            self._last_write[key + "_mtime"] = os.path.getmtime(path)
                            print(f"Migrated legacy state for '{key}' to scoped work item '{work_item_id}'")
                    except Exception as e:
                        print(f"Error migrating legacy state for '{key}': {e}")
                        pass

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
                import time
                for idx in range(10):
                    try:
                        os.replace(tmp_path, path)
                        break
                    except PermissionError as pe:
                        if idx == 9:
                            raise pe
                        time.sleep(0.05)
                
                # Backward compatibility sync for Dashboard UI
                if key == "workflow":
                    try:
                        import shutil
                        root_workflow_path = os.path.join(self.root_dir, "workflow.json")
                        shutil.copy2(path, root_workflow_path)
                    except Exception:
                        pass
                        
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
                    import time
                    for idx in range(10):
                        try:
                            os.replace(tmp_path, path)
                            break
                        except PermissionError:
                            if idx == 9:
                                raise
                            time.sleep(0.05)
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

def get_active_work_item_id() -> str | None:
    env_id = os.environ.get("AIWF_WORK_ITEM_ID") or os.environ.get("AIWF_ACTIVE_WORK_ITEM")
    if env_id:
        return env_id
    
    root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    active_path = os.path.join(root_dir, "active-work-items.json")
    if os.path.exists(active_path):
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_work_item_id")
        except Exception:
            pass
    return None

def set_active_work_item_id(work_item_id: str) -> None:
    root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    active_path = os.path.join(root_dir, "active-work-items.json")
    os.makedirs(root_dir, exist_ok=True)
    
    data = {"active_work_item_id": work_item_id, "work_items": {}}
    if os.path.exists(active_path):
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    data["active_work_item_id"] = work_item_id
    
    temp_path = active_path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, active_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

def register_work_item(work_item_id: str, workflow_type: str = None, status: str = "active", checkpoint: int = 1, parent_workflow_id: str = None) -> None:
    root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    active_path = os.path.join(root_dir, "active-work-items.json")
    os.makedirs(root_dir, exist_ok=True)
    
    data = {"active_work_item_id": work_item_id, "work_items": {}}
    if os.path.exists(active_path):
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    if "work_items" not in data:
        data["work_items"] = {}
        
    data["active_work_item_id"] = work_item_id
    
    data["work_items"][work_item_id] = {
        "work_item_id": work_item_id,
        "workflow_id": f"WF-{work_item_id}",
        "workflow_type": workflow_type or data["work_items"].get(work_item_id, {}).get("workflow_type", "unknown"),
        "status": status,
        "checkpoint": checkpoint,
        "parent_workflow_id": parent_workflow_id or data["work_items"].get(work_item_id, {}).get("parent_workflow_id"),
        "updated_at": datetime.now().astimezone().isoformat()
    }
    
    temp_path = active_path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, active_path)
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

# Global state store registry resolved based on env/mode
_store_instance = None

def get_state_store() -> StateStore:
    global _store_instance
    if "PYTEST_CURRENT_TEST" in os.environ:
        mode = os.environ.get("AIWF_RUNTIME_MODE", "normal").lower()
        if mode == "test-isolated":
            return InMemoryStateStore()
        root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
        return AtomicFileStateStore(root_dir)

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
