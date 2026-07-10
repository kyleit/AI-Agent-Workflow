# lock_manager.py
"""
File lock registry manager for AIWF safe implementation orchestrator.
Manages file-locks.json with all-or-nothing acquisition semantics.
Cross-platform PID liveness check via os.kill(pid, 0).
Rejects absolute paths and path traversal (SecurityError).
"""
import os
import threading
from datetime import datetime, timezone
from typing import Optional

from atomic_writer import write_json_atomic, read_json_safe  # type: ignore
from state_path import SecurityError  # type: ignore  # noqa: F401

LOCKS_FILE = os.path.join(".agents", "runtime", "file-locks.json")

_ACQUIRE_LOCK = threading.Lock()  # Module-level mutex for atomic acquisition


class FileLockConflict(RuntimeError):
    """Raised when a lock acquisition fails due to existing locks."""
    pass


class LockManager:
    """
    All-or-nothing file lock registry.
    Uses atomic file writes to persist lock state.
    Detects stale locks via PID liveness check.
    """

    def __init__(self, workspace_root: Optional[str] = None):
        self._workspace_root = workspace_root
        if workspace_root:
            self._path = os.path.join(workspace_root, LOCKS_FILE)
        else:
            self._path = LOCKS_FILE

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def acquire(
        self,
        task_id: str,
        write_set: list[str],
        pid: int,
        expires_seconds: int = 300,
    ) -> bool:
        """
        Acquire locks on all files in write_set for task_id.
        ALL-OR-NOTHING: if any file is locked, NO locks are acquired.
        
        Args:
            task_id: ID of the task acquiring the locks.
            write_set: List of relative file paths to lock.
            pid: PID of the owning process.
            expires_seconds: Lock expiry time in seconds.
        
        Returns:
            True if all locks acquired; False if any conflict.
        
        Raises:
            SecurityError: If write_set contains absolute paths or traversal.
        """
        # Validate paths
        validated = []
        for path in write_set:
            validated.append(self._validate_path(path))

        if not validated:
            return True  # No files to lock = success

        with _ACQUIRE_LOCK:
            # Clear stale locks first
            self.clear_stale_locks()

            # Load current locks
            data = self._load()
            locks = data.get("locks", {})

            # Check for conflicts (all-or-nothing)
            for path in validated:
                existing = locks.get(path)
                if existing and existing.get("status") == "active":
                    # Double-check it's not stale (PID could have died since load)
                    if not self.is_stale(existing):
                        return False

            # No conflicts — acquire all
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
        """
        Remove all locks owned by task_id.
        Returns list of released file paths.
        """
        with _ACQUIRE_LOCK:
            data = self._load()
            locks = data.get("locks", {})
            released = [
                path for path, ld in locks.items()
                if ld.get("task_id") == task_id
            ]
            for path in released:
                del locks[path]
            data["locks"] = locks
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)
        return released

    def is_stale(self, lock_entry: dict) -> bool:
        """
        Check if a lock is stale (owning PID is dead or lock expired).
        Uses os.kill(pid, 0) — raises OSError if PID does not exist.
        """
        # Check expiry time first (fastest check)
        expires_at_str = lock_entry.get("expires_at")
        if expires_at_str:
            try:
                from datetime import datetime as _dt
                expires_at = _dt.fromisoformat(expires_at_str)
                if datetime.now(timezone.utc) > expires_at:
                    return True
            except (ValueError, TypeError):
                pass

        # Check PID liveness
        pid = lock_entry.get("pid")
        if pid is None:
            return True  # No PID recorded = treat as stale

        try:
            os.kill(int(pid), 0)
            return False  # PID alive
        except (OSError, ProcessLookupError):
            return True  # PID dead = stale
        except (ValueError, TypeError):
            return True  # Invalid PID = stale

    def clear_stale_locks(self) -> list[str]:
        """
        Find and remove all stale locks.
        Returns list of cleared file paths.
        """
        data = self._load()
        locks = data.get("locks", {})
        stale = [
            path for path, ld in locks.items()
            if self.is_stale(ld)
        ]
        for path in stale:
            del locks[path]
        if stale:
            data["locks"] = locks
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save(data)
        return stale

    def get_active_locks(self) -> list[dict]:
        """Return all non-stale active lock entries."""
        self.clear_stale_locks()
        data = self._load()
        locks = data.get("locks", {})
        return [
            {"file_path": path, **ld}
            for path, ld in locks.items()
            if ld.get("status") == "active"
        ]

    def has_conflict(self, write_set: list[str]) -> bool:
        """
        Check if any file in write_set is currently locked.
        Clears stale locks first.
        """
        self.clear_stale_locks()
        data = self._load()
        locks = data.get("locks", {})
        for path in write_set:
            try:
                normalized = self._validate_path(path)
            except Exception:
                continue
            if normalized in locks and locks[normalized].get("status") == "active":
                return True
        return False

    def get_lock_count(self) -> int:
        """Return count of active (non-stale) locks."""
        return len(self.get_active_locks())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        data = read_json_safe(self._path)
        if not isinstance(data, dict):
            return {"version": "1.0.0", "locks": {}, "updated_at": ""}
        return data

    def _save(self, data: dict) -> None:
        parent = os.path.dirname(self._path)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        write_json_atomic(self._path, data)

    def _validate_path(self, path: str) -> str:
        """Validate and normalize a file path. Raises SecurityError if invalid."""
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
