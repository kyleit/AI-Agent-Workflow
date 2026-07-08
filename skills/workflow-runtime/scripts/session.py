# session.py
import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Any  # type: ignore

SESSION_FILE = os.path.join(".agents", ".session.json")
BAK_SESSION_FILE = SESSION_FILE + ".bak"
TMP_SESSION_FILE = SESSION_FILE + ".tmp"

def get_session_path() -> str:
    return os.path.abspath(SESSION_FILE)

def load_session() -> dict[str, Any]:  # type: ignore
    def _read_file(path: str) -> dict[str, Any]:  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("Empty file")
            res = json.loads(content)
            if not isinstance(res, dict):
                raise ValueError("Not a dictionary")
            return res  # type: ignore

    # 1. Try reading the main session file
    if os.path.exists(SESSION_FILE):
        try:
            return _read_file(SESSION_FILE)
        except (json.JSONDecodeError, IOError, ValueError):
            # Main file exists but is corrupted, try fallback to backup
            if os.path.exists(BAK_SESSION_FILE):
                try:
                    backup_data = _read_file(BAK_SESSION_FILE)
                    if backup_data:
                        # Auto-restore corrupted file
                        save_session_atomic(backup_data)
                        return backup_data
                except (json.JSONDecodeError, IOError, ValueError):
                    pass
    return {}

def save_session_atomic(data: dict[str, Any]) -> None:  # type: ignore
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    
    # Read existing session safely for preserving defaults
    existing: dict[str, Any] = {}  # type: ignore
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)  # type: ignore
        except (json.JSONDecodeError, IOError):
            pass

    # Copy input data to prevent mutation
    new_data = dict(data)
    
    # Preserve conversation_id if not present in new data
    if "conversation_id" not in new_data or not new_data["conversation_id"]:
        new_data["conversation_id"] = existing.get("conversation_id", str(uuid.uuid4()))
        
    # Default permission mode fields if not present in new data
    if "permission_mode" not in new_data:
        new_data["permission_mode"] = existing.get("permission_mode", "sandbox")
        new_data["permission_mode_selected_at"] = existing.get("permission_mode_selected_at", datetime.now().astimezone().isoformat())
        new_data["permission_mode_selected_by"] = existing.get("permission_mode_selected_by", "system")
    
    # Update timestamp
    new_data["updated_at"] = datetime.now().astimezone().isoformat()
    
    # 1. Create a backup of the current stable session file if it exists and is valid
    if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 0:
        try:
            shutil.copy2(SESSION_FILE, BAK_SESSION_FILE)
        except IOError:
            pass
            
    # 2. Write to tmp file
    try:
        with open(TMP_SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)
        
        # 3. Atomic rename/replace
        if os.path.exists(SESSION_FILE):
            os.replace(TMP_SESSION_FILE, SESSION_FILE)
        else:
            os.rename(TMP_SESSION_FILE, SESSION_FILE)
    except IOError:
        if os.path.exists(TMP_SESSION_FILE):
            try:
                os.remove(TMP_SESSION_FILE)
            except Exception:
                pass

SESSION_LOCK_FILE = SESSION_FILE + ".lock"

def acquire_session_lock(timeout: float = 10.0, delay: float = 0.05) -> None:
    import time
    os.makedirs(os.path.dirname(SESSION_LOCK_FILE), exist_ok=True)
    start_time = time.time()
    while True:
        try:
            # Exclusive file creation acts as a lock
            fd = os.open(SESSION_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            # Check timeout
            if time.time() - start_time > timeout:
                # Stale lock cleanup (if process died without unlocking)
                try:
                    os.remove(SESSION_LOCK_FILE)
                except Exception:
                    pass
            time.sleep(delay)

def release_session_lock() -> None:
    try:
        if os.path.exists(SESSION_LOCK_FILE):
            os.remove(SESSION_LOCK_FILE)
    except Exception:
        pass

class SessionLock:
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        
    def __enter__(self) -> "SessionLock":
        acquire_session_lock(timeout=self.timeout)
        return self
        
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        release_session_lock()

