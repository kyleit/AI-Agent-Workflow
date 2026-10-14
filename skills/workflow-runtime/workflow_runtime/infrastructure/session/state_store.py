# state_store.py
import atexit
import json
import os
import re
import tempfile
import uuid
from datetime import datetime
from typing import cast


class RevisionConflictError(Exception):
    def __init__(self, key: str, expected_revision: int, actual_revision: int):
        super().__init__(f"CAS revision conflict for '{key}': expected {expected_revision}, got {actual_revision}")
        self.key = key
        self.expected_revision = expected_revision
        self.actual_revision = actual_revision

class StateStore:
    def get(self, key: str) -> dict[str, object]:
        raise NotImplementedError

    def set(self, key: str, data: dict[str, object], expected_revision: int | None = None, force: bool = False) -> int:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

class NullStateStore(StateStore):
    def get(self, key: str) -> dict[str, object]:
        return {}
    def set(self, key: str, data: dict[str, object], expected_revision: int | None = None, force: bool = False) -> int:
        return 1
    def delete(self, key: str) -> bool:
        return True

class InMemoryStateStore(StateStore):
    def __init__(self) -> None:
        self.store: dict[str, dict[str, object]] = {}

    def get(self, key: str) -> dict[str, object]:
        return self.store.get(key, {})

    def set(self, key: str, data: dict[str, object], expected_revision: int | None = None, force: bool = False) -> int:
        current = self.store.get(key, {})
        raw_meta = current.get("_metadata", {})
        current_meta = cast(dict[str, object], raw_meta) if isinstance(raw_meta, dict) else {}
        actual_rev = int(str(current_meta.get("revision", 0)))

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
    def __init__(self, root_dir: str, work_item_id: str | None = None) -> None:
        self.root_dir = os.path.abspath(root_dir)
        selected = work_item_id or os.environ.get("AIWF_WORK_ITEM_ID") or os.environ.get("AIWF_ACTIVE_WORK_ITEM")
        if selected and not re.fullmatch(r"(?:FEAT|FIX|QUICK)-[0-9]+", selected):
            raise ValueError("CONTEXT_MISMATCH")
        self.work_item_id = selected
        self._cache: dict[str, dict[str, object]] = {}
        self._dirty: set[str] = set()
        self._last_write: dict[str, float] = {}

    def _get_path(self, key: str) -> str:
        if os.path.basename(key) != key or key in {"", ".", ".."}:
            raise ValueError("CONTEXT_MISMATCH")
        base = key if key.endswith(".json") else key + ".json"
        scoped = {"workflow", "runtime", "tasks", "agents", "locks", "handoffs", "checkpoints",
                  "timeline", "authorization", "approvals", "usage"}
        selected = self.work_item_id
        # Unbound stores retain the old display view; explicit contexts never migrate.
        if selected is None and key != "workflow":
            selected = get_active_work_item_id()
        path = os.path.join(self.root_dir, "work-items", selected, base) if selected and key in scoped else os.path.join(self.root_dir, base)
        if os.path.commonpath([os.path.realpath(path), os.path.realpath(self.root_dir)]) != os.path.realpath(self.root_dir):
            raise ValueError("CONTEXT_MISMATCH")
        return path

    def get(self, key: str) -> dict[str, object]:
        path = self._get_path(key)
        try:
            with open(path, encoding="utf-8-sig") as stream:
                value: object = json.load(stream)
            if isinstance(value, dict):
                return cast(dict[str, object], value)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}

    def set(self, key: str, data: dict[str, object], expected_revision: int | None = None, force: bool = False) -> int:
        path = self._get_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        lock = path + ".lock"
        # O_EXCL guards the complete read/CAS/replace transaction, not just replace.
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(descriptor)
        try:
            current = self.get(key)
            raw_meta = current.get("_metadata", {})
            meta = cast(dict[str, object], raw_meta) if isinstance(raw_meta, dict) else {}
            actual = int(str(meta.get("revision", 0)))
            if expected_revision is not None and expected_revision != actual:
                raise RevisionConflictError(key, expected_revision, actual)
            new = dict(data)
            new["_metadata"] = {"generation": meta.get("generation", 1), "revision": actual + 1,
                                "writer_id": f"{os.getpid()}-{uuid.uuid4().hex[:8]}",
                                "updated_at": datetime.now().astimezone().isoformat()}
            fd, temporary = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump(new, stream, indent=2, ensure_ascii=False)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)
            self._cache[key] = new
            return actual + 1
        finally:
            os.unlink(lock)

    def flush(self) -> None:
        # Writes are already durable. Retained for existing callers.
        return None

    def delete(self, key: str) -> bool:
        path = self._get_path(key)
        if not os.path.exists(path):
            return False
        descriptor = os.open(path + ".lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(descriptor)
        try:
            os.unlink(path)
            self._cache.pop(key, None)
            return True
        finally:
            os.unlink(path + ".lock")


def get_active_work_item_id() -> str | None:
    env_id = os.environ.get("AIWF_WORK_ITEM_ID") or os.environ.get("AIWF_ACTIVE_WORK_ITEM")
    if env_id:
        return env_id

    root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    workflow_path = os.path.join(root_dir, "workflow.json")
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            workflow = json.load(f)
        active = cast(dict[str, object], workflow).get("active_workflow") if isinstance(workflow, dict) else None
        if active:
            return str(active)
    except (OSError, ValueError):
        pass

    active_path = os.path.join(root_dir, "active-work-items.json")
    if os.path.exists(active_path):
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                value = cast(dict[str, object], data).get("active_work_item_id")
                return value if isinstance(value, str) else None
        except Exception:
            pass
    return None

def set_active_work_item_id(work_item_id: str) -> None:
    root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    active_path = os.path.join(root_dir, "active-work-items.json")
    os.makedirs(root_dir, exist_ok=True)

    data: dict[str, object] = {"active_work_item_id": work_item_id, "work_items": {}}
    if os.path.exists(active_path):
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = cast(dict[str, object], loaded)
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

def register_work_item(work_item_id: str, workflow_type: str | None = None, status: str = "active", checkpoint: int = 1, parent_workflow_id: str | None = None) -> None:
    root_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    active_path = os.path.join(root_dir, "active-work-items.json")
    os.makedirs(root_dir, exist_ok=True)

    data: dict[str, object] = {"active_work_item_id": work_item_id, "work_items": {}}
    if os.path.exists(active_path):
        try:
            with open(active_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    data = cast(dict[str, object], loaded)
        except Exception:
            pass

    work_items = cast(dict[str, object], data.setdefault("work_items", {}))
    existing_item = cast(dict[str, object], work_items.get(work_item_id, {}))

    data["active_work_item_id"] = work_item_id
    work_items[work_item_id] = {
        "work_item_id": work_item_id,
        "workflow_id": f"WF-{work_item_id}",
        "workflow_type": workflow_type or existing_item.get("workflow_type", "unknown"),
        "status": status,
        "checkpoint": checkpoint,
        "parent_workflow_id": parent_workflow_id or existing_item.get("parent_workflow_id"),
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
_store_instance: StateStore | None = None
_store_instances: dict[tuple[str, str | None, str], StateStore] = {}

def get_state_store() -> StateStore:
    root = os.path.abspath(os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state")))
    item = os.environ.get("AIWF_WORK_ITEM_ID") or os.environ.get("AIWF_ACTIVE_WORK_ITEM")
    mode = os.environ.get("AIWF_RUNTIME_MODE", "normal").lower()
    if _store_instance is not None:
        return _store_instance
    key = (root, item, mode)
    if key not in _store_instances:
        if os.environ.get("AIWF_DISABLE_STATE_WRITES", "false").lower() == "true" or mode == "test-memory":
            _store_instances[key] = NullStateStore()
        elif mode == "test-isolated":
            _store_instances[key] = InMemoryStateStore()
        else:
            _store_instances[key] = AtomicFileStateStore(root, item)
    return _store_instances[key]


def reset_state_store(store: StateStore | None = None) -> None:
    global _store_instance
    _store_instance = store
    _store_instances.clear()

def flush_stores() -> None:
    stores = list(_store_instances.values()) + ([_store_instance] if _store_instance else [])
    for store in stores:
        flush = getattr(store, "flush", None)
        if callable(flush):
            flush()
    store = get_state_store()
    if hasattr(store, "flush"):
        try:
            getattr(store, "flush")()
        except Exception:
            pass

# Flush all changes to disk on normal exit
atexit.register(flush_stores)
