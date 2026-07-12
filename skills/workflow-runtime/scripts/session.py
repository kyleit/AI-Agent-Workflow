# session.py
import os
import sys
import json
import uuid
import shutil
import tempfile
from datetime import datetime
from typing import Any  # type: ignore

# Tránh circular import bằng cách import động trong hàm hoặc import ở đây nếu an toàn
from state_sync import aggregate_state, deconstruct_state

def get_project_permission_config_path() -> str:
    root = os.environ.get("AIWF_PERMISSION_CONFIG_ROOT", "")
    if root:
        return os.path.abspath(os.path.join(root, "permissions.json"))
    return os.path.abspath(os.path.join(".agents", "config", "permissions.json"))

def load_project_permissions() -> dict[str, Any] | None:
    path = get_project_permission_config_path()
    if not os.path.exists(path):
        if os.environ.get("AIWF_TESTING_PERMISSIONS") == "true":
            return None
        mode = os.environ.get("AIWF_RUNTIME_MODE", "normal").lower()
        if "PYTEST_CURRENT_TEST" in os.environ or mode in ["test-memory", "test-isolated"]:
            return {
                "schema_version": "1.0.0",
                "initialized": True,
                "mode": "sandbox",
                "config_revision": 1,
                "initialized_at": datetime.now().astimezone().isoformat(),
                "updated_at": datetime.now().astimezone().isoformat(),
                "updated_by": "test",
                "source": "mock"
            }
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return None

def write_project_permissions_atomic(data: dict[str, Any]) -> None:
    path = get_project_permission_config_path()
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(dir=dir_name or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise e

def validate_permissions_data(data: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "Configuration must be a JSON object."
    required = ["schema_version", "initialized", "mode"]
    for field in required:
        if field not in data:
            return False, f"Missing required field: '{field}'."
    mode = data.get("mode")
    if mode not in ["sandbox", "full_access", "unrestricted"]:
        return False, f"Invalid permission mode: '{mode}'."
    return True, "Valid"

def get_default_authorization_state(permission_mode: str, work_item_id: str = None) -> dict[str, Any]:
    if not work_item_id:
        work_item_id = os.environ.get("AIWF_ACTIVE_WORK_ITEM") or os.environ.get("AIWF_WORK_ITEM_ID") or "WF-GLOBAL"
        
    permissions = load_project_permissions() or {}
    perm_cfg = permissions.get("permissions", {})
    
    is_full = (permission_mode == "full_access") or (perm_cfg.get("default_mode") == "full_access" and perm_cfg.get("autonomous_delivery", True))
    
    allowed_phases = [
        "discovery", "brainstorming", "planning", "blueprint",
        "architecture_validation", "implementation", "debug", "test",
        "browser_validation", "verification", "final_review"
    ] if is_full else []
    
    return {
        "authorization_id": f"AUTH-{work_item_id}",
        "project_id": permissions.get("project_id", "ai-skill-framework"),
        "workspace_id": permissions.get("workspace_id", "workspace-id"),
        "work_item_id": work_item_id,
        "workflow_id": f"WF-{work_item_id}",
        "permission_mode": permission_mode,
        "authorization_status": "active" if is_full else "inactive",
        "source": "explicit_user_request" if is_full else "system_default",
        "allowed_phases": allowed_phases,
        "allow_document_create": is_full,
        "allow_document_modify": is_full,
        "allow_source_create": is_full,
        "allow_source_modify": is_full,
        "allow_test_create": is_full,
        "allow_test_modify": is_full,
        "allow_runtime_state_modify": is_full,
        "allow_agent_spawn": is_full,
        "allow_agent_reassignment": is_full,
        "allow_parallel_execution": is_full,
        "allow_retry": is_full,
        "allow_replan": is_full,
        "allow_commit": False,
        "allow_merge": False,
        "allow_rebase": False,
        "allow_tag": False,
        "allow_push": False,
        "allow_release": False,
        "allow_publish": False,
        "allow_deploy": False,
        "stop_at": "release_approval",
        "expires_when": "release_approved_or_work_item_cancelled",
        "created_at": datetime.now().astimezone().isoformat(),
        "terminated_at": None,
        "max_retries_per_task": perm_cfg.get("max_retries_per_task", 3),
        "max_replans_per_work_item": perm_cfg.get("max_replans_per_work_item", 2),
        "max_agent_reassignments_per_task": perm_cfg.get("max_agent_reassignments_per_task", 2)
    }

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
    state_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    context_file = os.path.join(state_dir, "context.json")
    session_file = os.path.join(state_dir, ".session.json") if "AIWF_STATE_ROOT" in os.environ else SESSION_FILE
    
    session_data = {}
    
    # Check if session_file exists and is newer/equal to context_file (for test mocks)
    use_legacy_file = False
    if os.path.exists(session_file):
        if not os.path.exists(context_file):
            use_legacy_file = True
        else:
            try:
                session_mtime = os.path.getmtime(session_file)
                context_mtime = os.path.getmtime(context_file)
                if session_mtime >= context_mtime - 2:
                    use_legacy_file = True
            except Exception:
                pass

    if use_legacy_file:
        try:
            with open(session_file, "r", encoding="utf-8") as f:
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
        
        # Đồng bộ từ permissions.json nếu có
        permissions = load_project_permissions()
        if permissions:
            session_data["permission_mode"] = permissions.get("mode", "sandbox")
            session_data["permission_mode_selected_at"] = permissions.get("updated_at")
            session_data["permission_mode_selected_by"] = permissions.get("updated_by")
            
        # Nạp hoặc khởi tạo active authorization state
        mode = session_data.get("permission_mode", "sandbox")
        work_item_id = session_data.get("work_item", {}).get("id") or os.environ.get("AIWF_WORK_ITEM_ID", "default_work_item")
        if "authorization" not in session_data or session_data["authorization"] is None or session_data["authorization"].get("permission_mode") != mode:
            session_data["authorization"] = get_default_authorization_state(mode, work_item_id)
            
        return session_data
        
    return {}

def save_session_atomic(data: dict[str, Any]) -> None:  # type: ignore
    from state_store import RevisionConflictError
    import time
    
    state_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    session_file = os.path.join(state_dir, ".session.json") if "AIWF_STATE_ROOT" in os.environ else SESSION_FILE
    bak_session_file = session_file + ".bak"
    tmp_session_file = session_file + ".tmp"
    
    retries = 3
    while retries > 0:
        try:
            existing = load_session()
            new_data = dict(existing)
            new_data.update(data)
            
            if "conversation_id" not in new_data or not new_data["conversation_id"]:
                new_data["conversation_id"] = existing.get("conversation_id", str(uuid.uuid4()))
                
            if "permission_mode" not in new_data:
                new_data["permission_mode"] = existing.get("permission_mode", "sandbox")
                new_data["permission_mode_selected_at"] = existing.get("permission_mode_selected_at", datetime.now().astimezone().isoformat())
                new_data["permission_mode_selected_by"] = existing.get("permission_mode_selected_by", "user")
            
            mode = new_data.get("permission_mode", "sandbox")
            work_item_id = new_data.get("work_item", {}).get("id") or os.environ.get("AIWF_WORK_ITEM_ID", "default_work_item")
            if "authorization" not in new_data or new_data["authorization"] is None or new_data["authorization"].get("permission_mode") != mode:
                new_data["authorization"] = get_default_authorization_state(mode, work_item_id)

            new_data["updated_at"] = datetime.now().astimezone().isoformat()
            
            # 1. Ghi rã trạng thái vào các file trạng thái con
            deconstruct_state(".", new_data)
            
            # 2. Xóa tệp .session.json trên đĩa để chuyển sang chế độ Pure Split State hoàn toàn
            for path_to_remove in [session_file, bak_session_file, tmp_session_file]:
                if os.path.exists(path_to_remove):
                    try:
                        os.remove(path_to_remove)
                    except Exception:
                        pass
            return
        except RevisionConflictError as e:
            retries -= 1
            if retries <= 0:
                raise
            time.sleep(0.05)  # exponential backoff / delay


SESSION_LOCK_FILE = SESSION_FILE + ".lock"

def acquire_session_lock(timeout: float = 10.0, delay: float = 0.05) -> None:
    import time
    state_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    lock_file = os.path.join(state_dir, ".session.json.lock") if "AIWF_STATE_ROOT" in os.environ else SESSION_LOCK_FILE
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    start_time = time.time()
    while True:
        try:
            fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            return
        except FileExistsError:
            # Check if the process holding the lock is dead
            try:
                if os.path.exists(lock_file):
                    with open(lock_file, "r") as f:
                        pid_str = f.read().strip()
                    if pid_str:
                        from lease import is_process_alive
                        pid = int(pid_str)
                        if not is_process_alive(pid):
                            try:
                                os.remove(lock_file)
                            except Exception:
                                pass
            except Exception:
                pass

            if time.time() - start_time > timeout:
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
            time.sleep(delay)

def release_session_lock() -> None:
    state_dir = os.environ.get("AIWF_STATE_ROOT", os.path.join(".agents", "state"))
    lock_file = os.path.join(state_dir, ".session.json.lock") if "AIWF_STATE_ROOT" in os.environ else SESSION_LOCK_FILE
    try:
        if os.path.exists(lock_file):
            os.remove(lock_file)
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


# ---------------------------------------------------------------------------
# FEAT-050: Lightweight Runtime Initialization — Session Helpers
# ---------------------------------------------------------------------------

def load_guardrails_summary() -> dict:
    """
    Compute SHA-256 hashes of AI_RULES.md, .agents/AGENTS.md, and active SKILL.md.
    Returns policy_flags dict. Does NOT re-load or re-enforce full rule text.
    Hash confirms integrity only — fast and lightweight.
    """
    import hashlib

    def _sha256(path: str) -> str:
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    rules_path = "AI_RULES.md"
    agents_path = os.path.join(".agents", "AGENTS.md")

    # Detect active skill from runtime state
    runtime_path = os.path.join(".agents", "state", "runtime.json")
    skill_path = ""
    try:
        if os.path.exists(runtime_path):
            with open(runtime_path, "r", encoding="utf-8") as f:
                runtime_data = json.load(f)
            current_skill = runtime_data.get("current_skill", "initialize-workflow")
            for base in ["skills", os.path.join(".agents", "skills")]:
                candidate = os.path.join(base, current_skill, "SKILL.md")
                if os.path.exists(candidate):
                    skill_path = candidate
                    break
    except Exception:
        pass

    return {
        "rules_loaded": os.path.exists(rules_path),
        "ai_rules_hash": _sha256(rules_path),
        "agents_hash": _sha256(agents_path),
        "active_skill_hash": _sha256(skill_path),
        "active_skill_path": skill_path,
        "policy_flags": {
            "approval_gate": True,
            "git_gate": True,
            "blueprint_gate": True,
            "release_gate": True,
            "testing_gate": True,
            "workspace_permission_gate": True,
        },
    }


def load_approval_state() -> dict:
    """
    Read .agents/state/approvals.json.
    Returns empty dict if file missing (non-blocking for optional mode).
    """
    approvals_path = os.path.join(".agents", "state", "approvals.json")
    if not os.path.exists(approvals_path):
        return {}
    try:
        with open(approvals_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_dashboard_state() -> dict:
    """
    Read .agents/state/dashboard.json.
    Returns empty dict if file missing.
    Used for: release_allowed flag, provider info, usage summary.
    """
    dashboard_path = os.path.join(".agents", "state", "dashboard.json")
    if not os.path.exists(dashboard_path):
        return {}
    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


import hashlib

def get_project_identity(project_path=".") -> dict:
    abs_path = os.path.abspath(project_path)
    # project_id
    project_id = "ai-skill-framework"
    profile_path = os.path.join(abs_path, ".agents", "project-profile.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                prof_data = json.load(f)
            project_id = prof_data.get("project_id", project_id)
        except Exception:
            pass
    # workspace_id
    workspace_id = os.path.basename(abs_path)
    # project_root_hash
    project_root_hash = hashlib.sha256(abs_path.encode("utf-8")).hexdigest()
    
    return {
        "project_id": project_id,
        "workspace_id": workspace_id,
        "project_root_hash": project_root_hash
    }


class OSFileLock:
    def __init__(self, lock_path: str):
        self.lock_path = os.path.abspath(lock_path)
        self.file_handle = None

    def acquire(self) -> bool:
        try:
            os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
            self.file_handle = open(self.lock_path, "w")
            
            # Platform specific lock
            try:
                import fcntl
                fcntl.flock(self.file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except ImportError:
                import msvcrt
                self.file_handle.seek(0)
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except (ImportError, OSError):
            self.release()
            return False

    def release(self):
        if self.file_handle:
            try:
                try:
                    import fcntl
                    fcntl.flock(self.file_handle, fcntl.LOCK_UN)
                except ImportError:
                    try:
                        import msvcrt
                        self.file_handle.seek(0)
                        msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    except (ImportError, OSError):
                        pass
                self.file_handle.close()
            except Exception:
                pass
            finally:
                self.file_handle = None
            try:
                if os.path.exists(self.lock_path):
                    os.remove(self.lock_path)
            except Exception:
                pass


DEFAULT_CLIENT_POLICY = {
    "max_interactive_clients": 1,
    "detach_previous_on_new_attach": True,
    "preserve_background_workers": True
}

DEFAULT_RESOURCE_LIMITS = {
    "max_cpu_percent": 85,
    "max_memory_percent": 80,
    "max_subagents": 8,
    "max_concurrency": 4,
    "max_spawn_per_minute": 10,
    "max_retries_per_task": 3,
    "max_restarts_per_10_minutes": 3,
    "poll_interval_ms": 500,
    "idle_backoff_ms": 1500
}

DEFAULT_TEST_EXECUTION = {
    "max_parallel_pytest_processes": 1,
    "max_pytest_workers": 2,
    "default_mode": "affected",
    "allow_full_suite_concurrency": False,
    "timeout_seconds": 1800,
    "retry_limit": 2,
    "kill_process_tree_on_timeout": True,
    "cooldown_seconds": 5
}

DEFAULT_SPAWN_LIMITS = {
    "max_total_subagents": 8,
    "max_subagents_per_work_item": 4,
    "max_spawn_per_minute": 10,
    "max_pending_spawns": 5,
    "max_spawn_depth": 1,
    "allow_subagent_spawn_subagent": False,
    "max_failed_spawn_retries": 2
}

def load_config_section(section_name: str, default_val: dict) -> dict:
    config_path = os.path.join(".agents", "workflow.config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if section_name in data:
                return data[section_name]
        except Exception:
            pass
    return default_val


DEFAULT_RUNTIME_POLICY = {
  "resource_limits": {
    "max_subagents": 4,
    "max_concurrency": 2,
    "max_spawn_per_minute": 4,
    "max_pending_spawns": 5,
    "max_parallel_pytest_processes": 1,
    "max_pytest_workers": 1,
    "cpu_warning_percent": 70,
    "cpu_throttle_percent": 80,
    "memory_warning_percent": 70,
    "memory_throttle_percent": 80,
    "memory_circuit_breaker_percent": 90
  },
  "scheduler": {
    "adaptive_concurrency": True,
    "pause_on_high_cpu": True,
    "pause_on_high_memory": True
  },
  "pytest": {
    "default_mode": "affected",
    "run_full_suite_only_at_final_review": True,
    "deduplicate_requests": True
  }
}


def get_runtime_policy_path() -> str:
    root = os.environ.get("AIWF_RUNTIME_POLICY_ROOT", "")
    if root:
        return os.path.abspath(os.path.join(root, "runtime-policy.json"))
    return os.path.abspath(os.path.join(".agents", "config", "runtime-policy.json"))


def validate_runtime_policy(policy: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(policy, dict):
        return False, "Policy must be a JSON object."
    
    sections = ["resource_limits", "scheduler", "pytest"]
    for s in sections:
        if s not in policy or not isinstance(policy[s], dict):
            return False, f"Missing or invalid section: '{s}'."
            
    # resource_limits keys validation
    rl_keys = {
        "max_subagents": int,
        "max_concurrency": int,
        "max_spawn_per_minute": int,
        "max_pending_spawns": int,
        "max_parallel_pytest_processes": int,
        "max_pytest_workers": int,
        "cpu_warning_percent": (int, float),
        "cpu_throttle_percent": (int, float),
        "memory_warning_percent": (int, float),
        "memory_throttle_percent": (int, float),
        "memory_circuit_breaker_percent": (int, float)
    }
    
    rl = policy["resource_limits"]
    for k, t in rl_keys.items():
        if k not in rl:
            return False, f"Missing key in resource_limits: '{k}'."
        if not isinstance(rl[k], t):
            return False, f"Invalid type for resource_limits.{k}: expected {t}, got {type(rl[k])}."
            
    # scheduler keys validation
    sch_keys = {
        "adaptive_concurrency": bool,
        "pause_on_high_cpu": bool,
        "pause_on_high_memory": bool
    }
    sch = policy["scheduler"]
    for k, t in sch_keys.items():
        if k not in sch:
            return False, f"Missing key in scheduler: '{k}'."
        if not isinstance(sch[k], t):
            return False, f"Invalid type for scheduler.{k}: expected {t}, got {type(sch[k])}."
            
    # pytest keys validation
    py_keys = {
        "default_mode": str,
        "run_full_suite_only_at_final_review": bool,
        "deduplicate_requests": bool
    }
    py = policy["pytest"]
    for k, t in py_keys.items():
        if k not in py:
            return False, f"Missing key in pytest: '{k}'."
        if not isinstance(py[k], t):
            return False, f"Invalid type for pytest.{k}: expected {t}, got {type(py[k])}."
            
    return True, "Valid"


def write_runtime_policy(policy: dict[str, Any]) -> None:
    path = get_runtime_policy_path()
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(dir=dir_name or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(policy, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise e


def load_runtime_policy(validate: bool = True) -> dict[str, Any]:
    path = get_runtime_policy_path()
    if not os.path.exists(path):
        write_runtime_policy(DEFAULT_RUNTIME_POLICY)
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            policy = json.load(f)
    except Exception as e:
        if validate:
            raise ValueError(f"Failed to parse runtime-policy.json: {e}")
        return DEFAULT_RUNTIME_POLICY
        
    if validate:
        ok, err = validate_runtime_policy(policy)
        if not ok:
            raise ValueError(f"Invalid runtime-policy.json schema: {err}")
            
    return policy



