# session.py
import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Any  # type: ignore

# Tránh circular import bằng cách import động trong hàm hoặc import ở đây nếu an toàn
from state_sync import aggregate_state, deconstruct_state

SESSION_FILE = os.path.join(".agents", ".session.json")
BAK_SESSION_FILE = SESSION_FILE + ".bak"
TMP_SESSION_FILE = SESSION_FILE + ".tmp"

def get_session_path() -> str:
    return os.path.abspath(SESSION_FILE)

def load_session() -> dict[str, Any]:  # type: ignore
    state_dir = os.path.join(".agents", "state")
    context_file = os.path.join(state_dir, "context.json")
    
    # 1. Nếu có state files, dùng cơ chế Aggregate để lấy session dữ liệu mới nhất
    if os.path.exists(context_file):
        if os.path.exists(SESSION_FILE):
            try:
                session_mtime = os.path.getmtime(SESSION_FILE)
                context_mtime = os.path.getmtime(context_file)
                if session_mtime > context_mtime + 0.001:
                    with open(SESSION_FILE, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            session_data = json.loads(content)
                            if isinstance(session_data, dict) and session_data:
                                deconstruct_state(".", session_data)
            except Exception:
                pass
        try:
            return aggregate_state(".")
        except Exception:
            pass

    # 2. Fallback sang đọc session.json cũ
    def _read_file(path: str) -> dict[str, Any]:  # type: ignore
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                raise ValueError("Empty file")
            res = json.loads(content)
            if not isinstance(res, dict):
                raise ValueError("Not a dictionary")
            return res  # type: ignore

    session_data = {}
    if os.path.exists(SESSION_FILE):
        try:
            session_data = _read_file(SESSION_FILE)
        except (json.JSONDecodeError, IOError, ValueError):
            if os.path.exists(BAK_SESSION_FILE):
                try:
                    backup_data = _read_file(BAK_SESSION_FILE)
                    if backup_data:
                        session_data = backup_data
                except (json.JSONDecodeError, IOError, ValueError):
                    pass
    
    if session_data:
        # Tự động di trú sang cấu trúc mới
        try:
            deconstruct_state(".", session_data)
        except Exception:
            pass
        return session_data
        
    return {}

def save_session_atomic(data: dict[str, Any]) -> None:  # type: ignore
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    
    existing: dict[str, Any] = {}  # type: ignore
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing = json.loads(content)  # type: ignore
        except (json.JSONDecodeError, IOError):
            pass

    new_data = dict(data)
    
    if "conversation_id" not in new_data or not new_data["conversation_id"]:
        new_data["conversation_id"] = existing.get("conversation_id", str(uuid.uuid4()))
        
    if "permission_mode" not in new_data:
        new_data["permission_mode"] = existing.get("permission_mode", "sandbox")
        new_data["permission_mode_selected_at"] = existing.get("permission_mode_selected_at", datetime.now().astimezone().isoformat())
        new_data["permission_mode_selected_by"] = existing.get("permission_mode_selected_by", "system")
    
    new_data["updated_at"] = datetime.now().astimezone().isoformat()
    
    # 1. Ghi rã trạng thái vào các file trạng thái con
    try:
        deconstruct_state(".", new_data)
    except Exception:
        pass
        
    # 2. Tổng hợp ngược lại session.json
    try:
        aggregate_state(".")
    except Exception:
        # Fallback ghi trực tiếp session.json nếu sync engine lỗi
        if os.path.exists(SESSION_FILE) and os.path.getsize(SESSION_FILE) > 0:
            try:
                shutil.copy2(SESSION_FILE, BAK_SESSION_FILE)
            except IOError:
                pass
        try:
            with open(TMP_SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(new_data, f, indent=2, ensure_ascii=False)
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
            fd = os.open(SESSION_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            if time.time() - start_time > timeout:
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

def load_workflow_config() -> dict[str, Any]:  # type: ignore
    config_path = os.path.join(".agents", "workflow.config.json")
    default_config = {
        "project_name": "unknown",
        "git_flow": {
            "development_branch": "main",
            "release_branch": "main",
            "sync_method": "merge",
            "extra_push_branches": []
        },
        "release_pipeline": {
            "steps": [
                "bump_version",
                "update_changelog",
                "git_commit",
                "git_tag",
                "custom_commands",
                "git_push"
            ],
            "custom_commands": {}
        }
    }
    if not os.path.exists(config_path):
        return default_config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                # Deep merge defaults
                for k, v in default_config.items():
                    if k not in data:
                        data[k] = v
                    elif isinstance(v, dict) and isinstance(data[k], dict):
                        for sub_k, sub_v in v.items():
                            if sub_k not in data[k]:
                                data[k][sub_k] = sub_v
                return data
    except Exception:
        pass
    return default_config

