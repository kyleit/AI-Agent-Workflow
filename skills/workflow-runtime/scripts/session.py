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

def migrate_session_schema(session: dict[str, Any]) -> None:
    if not session:
        return
    wf_summary = session.get("workflow_usage_summary", {})
    if isinstance(wf_summary, dict) and "active_context" in wf_summary:
        return
    legacy_wf = wf_summary if isinstance(wf_summary, dict) else {}
    legacy_ctx = session.get("context_usage", {})
    if not isinstance(legacy_ctx, dict):
        legacy_ctx = {}
    active_tokens = legacy_ctx.get("total_tokens") or legacy_wf.get("total_tokens") or 0
    limit_tokens = legacy_ctx.get("limit_tokens") or legacy_wf.get("limit_tokens") or 2000000
    percentage = legacy_ctx.get("percentage") or legacy_wf.get("percentage") or 0.0
    input_tokens = legacy_wf.get("input_tokens") or legacy_ctx.get("input_tokens") or int(active_tokens * 0.98)
    output_tokens = legacy_wf.get("output_tokens") or legacy_ctx.get("output_tokens") or int(active_tokens * 0.02)
    cache_tokens = legacy_wf.get("cache_tokens") or legacy_ctx.get("cache_tokens") or int(active_tokens * 0.15)
    thinking_tokens = legacy_wf.get("thinking_tokens") or legacy_ctx.get("thinking_tokens") or int(active_tokens * 0.005)
    active_context = {
        "total_tokens": active_tokens,
        "limit_tokens": limit_tokens,
        "percentage": percentage,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_tokens": cache_tokens,
        "thinking_tokens": thinking_tokens
    }
    accumulated_usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_tokens": cache_tokens,
        "thinking_tokens": thinking_tokens,
        "total_tokens": active_tokens,
        "estimated_cost_usd": legacy_wf.get("estimated_cost_usd") or round(active_tokens * 1.5 / 1000000, 4),
        "request_count": legacy_wf.get("request_count") or 1
    }
    efficiency = {
        "cache_hit_ratio": round(cache_tokens / max(1, input_tokens), 2),
        "input_to_output_ratio": round(input_tokens / max(1, output_tokens), 2),
        "growth_speed_tokens_per_request": 0.0,
        "duplicate_read_count": 0,
        "estimated_savings_usd": 0.0
    }
    session["workflow_usage_summary"] = {
        "total_tokens": active_tokens,
        "limit_tokens": limit_tokens,
        "percentage": percentage,
        "active_context": active_context,
        "accumulated_usage": accumulated_usage,
        "efficiency": efficiency
    }

def load_session() -> dict[str, Any]:  # type: ignore
    state_dir = os.path.join(".agents", "state")
    context_file = os.path.join(state_dir, "context.json")
    
    session_data = {}
    
    # Check if SESSION_FILE exists and is newer/equal to context_file (for test mocks)
    use_legacy_file = False
    if os.path.exists(SESSION_FILE):
        if not os.path.exists(context_file):
            use_legacy_file = True
        else:
            try:
                session_mtime = os.path.getmtime(SESSION_FILE)
                context_mtime = os.path.getmtime(context_file)
                if session_mtime >= context_mtime - 2:
                    use_legacy_file = True
            except Exception:
                pass

    if use_legacy_file:
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    session_data = json.loads(content)
                    if isinstance(session_data, dict) and session_data:
                        migrate_session_schema(session_data)
                        deconstruct_state(".", session_data)
        except Exception:
            pass

    if not session_data and os.path.exists(context_file):
        try:
            session_data = aggregate_state(".")
        except Exception:
            pass

    if session_data:
        migrate_session_schema(session_data)
        return session_data
        
    return {}

def save_session_atomic(data: dict[str, Any]) -> None:  # type: ignore
    existing = load_session()
    new_data = dict(data)
    
    if "conversation_id" not in new_data or not new_data["conversation_id"]:
        new_data["conversation_id"] = existing.get("conversation_id", str(uuid.uuid4()))
        
    if "permission_mode" not in new_data:
        new_data["permission_mode"] = existing.get("permission_mode", "sandbox")
        new_data["permission_mode_selected_at"] = existing.get("permission_mode_selected_at", datetime.now().astimezone().isoformat())
        new_data["permission_mode_selected_by"] = existing.get("permission_mode_selected_by", "user")
    
    new_data["updated_at"] = datetime.now().astimezone().isoformat()
    
    # 1. Ghi rã trạng thái vào các file trạng thái con
    try:
        deconstruct_state(".", new_data)
    except Exception:
        pass
        
    # 2. Xóa tệp .session.json trên đĩa để chuyển sang chế độ Pure Split State hoàn toàn
    for path_to_remove in [SESSION_FILE, BAK_SESSION_FILE, TMP_SESSION_FILE]:
        if os.path.exists(path_to_remove):
            try:
                os.remove(path_to_remove)
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

