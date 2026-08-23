from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Any, Optional, cast

from workflow_runtime.infrastructure.filesystem.atomic_writer import (
    read_json_safe, write_json_atomic)
from workflow_runtime.infrastructure.session.state_path import SecurityError

LOCKS_FILE = os.path.join(".agents", "runtime", "file-locks.json")
_ACQUIRE_LOCK = threading.Lock()


class FileLockConflict(RuntimeError):
    """Raised when a lock acquisition fails due to existing locks."""


class LockManager:
    """
    All-or-nothing file lock registry.
    Uses atomic file writes to persist lock state.
    Detects stale locks via PID liveness check.
    """

    def __init__(self, workspace_root: Optional[str] = None) -> None:
        self._workspace_root = workspace_root
        if workspace_root:
            self._path = os.path.join(workspace_root, LOCKS_FILE)
        else:
            self._path = LOCKS_FILE

    def acquire(
        self,
        task_id: str,
        write_set: list[str],
        pid: int,
        expires_seconds: int = 300,
    ) -> bool:
        validated: list[str] = []
        for path in write_set:
            validated.append(self._validate_path(path))

        if not validated:
            return True

        with _ACQUIRE_LOCK:
            self.clear_stale_locks()
            data = self._load()
            raw_locks = data.get("locks")
            locks: dict[str, Any] = cast(dict[str, Any], raw_locks) if isinstance(raw_locks, dict) else {}

            for path in validated:
                existing = cast(dict[str, Any], locks.get(path)) if isinstance(locks.get(path), dict) else None
                if existing and str(existing.get("status", "")) == "active":
                    if not self.is_stale(existing):
                        return False

            now = datetime.now(timezone.utc)
            expires_at = now.timestamp() + expires_seconds

            for path in validated:
                locks[path] = {
                    "task_id": task_id,
                    "pid": pid,
                    "locked_at": now.isoformat(),
                    "expires_at": datetime.fromtimestamp(
                        expires_at, tz=timezone.utc
                    ).isoformat(),
                    "status": "active",
                }

            data["locks"] = locks
            data["updated_at"] = now.isoformat()
            self._save(data)
            return True

    def release(self, task_id: str) -> list[str]:
        with _ACQUIRE_LOCK:
            data = self._load()
            raw_locks = data.get("locks")
            locks: dict[str, Any] = cast(dict[str, Any], raw_locks) if isinstance(raw_locks, dict) else {}
            released: list[str] = [
                path for path, ld in locks.items()
                if isinstance(ld, dict) and str(cast(dict[str, Any], ld).get("task_id", "")) == task_id
            ]
            for path in released:
                del locks[path]
            data["locks"] = locks
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)
        return released

    def is_stale(self, lock_entry: dict[str, Any]) -> bool:
        expires_at_str = str(lock_entry.get("expires_at", "") or "")
        if expires_at_str:
            try:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now(timezone.utc) > expires_at:
                    return True
            except (ValueError, TypeError):
                pass

        pid = lock_entry.get("pid")
        if pid is None:
            return True

        try:
            os.kill(int(str(pid)), 0)
            return False
        except (OSError, ProcessLookupError):
            return True
        except (ValueError, TypeError):
            return True

    def clear_stale_locks(self) -> list[str]:
        data = self._load()
        raw_locks = data.get("locks")
        locks: dict[str, Any] = cast(dict[str, Any], raw_locks) if isinstance(raw_locks, dict) else {}
        stale: list[str] = [
            path for path, ld in locks.items()
            if isinstance(ld, dict) and self.is_stale(cast(dict[str, Any], ld))
        ]
        for path in stale:
            del locks[path]
        if stale:
            data["locks"] = locks
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)
        return stale

    def get_active_locks(self) -> list[dict[str, Any]]:
        self.clear_stale_locks()
        data = self._load()
        raw_locks = data.get("locks")
        locks: dict[str, Any] = cast(dict[str, Any], raw_locks) if isinstance(raw_locks, dict) else {}
        return [
            {"file_path": path, **cast(dict[str, Any], ld)}
            for path, ld in locks.items()
            if isinstance(ld, dict) and str(cast(dict[str, Any], ld).get("status", "")) == "active"
        ]

    def has_conflict(self, write_set: list[str]) -> bool:
        self.clear_stale_locks()
        data = self._load()
        raw_locks = data.get("locks")
        locks: dict[str, Any] = cast(dict[str, Any], raw_locks) if isinstance(raw_locks, dict) else {}
        for path in write_set:
            try:
                normalized = self._validate_path(path)
            except Exception:
                continue
            entry = cast(dict[str, Any], locks.get(normalized)) if isinstance(locks.get(normalized), dict) else None
            if entry and str(entry.get("status", "")) == "active":
                return True
        return False

    def get_lock_count(self) -> int:
        return len(self.get_active_locks())

    def _load(self) -> dict[str, Any]:
        data = read_json_safe(self._path)
        if not isinstance(data, dict):
            return {"version": "1.0.0", "locks": {}, "updated_at": ""}
        return cast(dict[str, Any], data)

    def _save(self, data: dict[str, Any]) -> None:
        parent = os.path.dirname(self._path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        write_json_atomic(self._path, data)

    def _validate_path(self, path: str) -> str:
        if os.path.isabs(path):
            raise SecurityError(
                f"Absolute path rejected in write_set: '{path}'. "
                f"Only relative workspace paths allowed."
            )
        normalized = os.path.normpath(path)
        if normalized.startswith(".."):
            raise SecurityError(
                f"Path traversal rejected: '{path}'."
            )
        return normalized


__all__ = [
    "FileLockConflict",
    "LockManager",
]
