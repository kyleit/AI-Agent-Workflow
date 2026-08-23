from __future__ import annotations

import hashlib
import json
import os
import tempfile
from typing import Any, cast


class SessionLock:
    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def __enter__(self) -> SessionLock:
        from .session_io import acquire_session_lock
        acquire_session_lock(timeout=self.timeout)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        from .session_io import release_session_lock
        release_session_lock()


def load_workflow_config() -> dict[str, Any]:
    config_path = os.path.join(".agents", "workflow.config.json")
    default_config: dict[str, Any] = {
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
                data_dict = cast(dict[str, Any], data)
                for k, v in default_config.items():
                    if k not in data_dict:
                        data_dict[k] = v
                    elif isinstance(v, dict) and isinstance(data_dict.get(k), dict):
                        v_dict = cast(dict[str, Any], v)
                        sub_dict = cast(dict[str, Any], data_dict[k])
                        for sub_k, sub_v in v_dict.items():
                            if sub_k not in sub_dict:
                                sub_dict[sub_k] = sub_v
                        data_dict[k] = sub_dict
                return data_dict
    except Exception:
        pass
    return default_config


def load_guardrails_summary() -> dict[str, Any]:
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

    runtime_path = os.path.join(".agents", "state", "runtime.json")
    skill_path = ""
    try:
        if os.path.exists(runtime_path):
            with open(runtime_path, "r", encoding="utf-8") as f:
                runtime_data = json.load(f)
            if isinstance(runtime_data, dict):
                runtime_dict = cast(dict[str, Any], runtime_data)
                current_skill = str(runtime_dict.get("current_skill", "initialize-workflow"))
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


def load_approval_state() -> dict[str, Any]:
    approvals_path = os.path.join(".agents", "state", "approvals.json")
    if not os.path.exists(approvals_path):
        return {}
    try:
        with open(approvals_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def load_dashboard_state() -> dict[str, Any]:
    dashboard_path = os.path.join(".agents", "state", "dashboard.json")
    if not os.path.exists(dashboard_path):
        return {}
    try:
        with open(dashboard_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_project_identity(project_path: str = ".") -> dict[str, Any]:
    abs_path = os.path.abspath(project_path)
    project_id = "ai-skill-framework"
    profile_path = os.path.join(abs_path, ".agents", "project-profile.json")
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                prof_data = json.load(f)
            if isinstance(prof_data, dict):
                prof_dict = cast(dict[str, Any], prof_data)
                project_id = str(prof_dict.get("project_id", project_id))
        except Exception:
            pass
    workspace_id = os.path.basename(abs_path)
    project_root_hash = hashlib.sha256(abs_path.encode("utf-8")).hexdigest()

    return {
        "project_id": project_id,
        "workspace_id": workspace_id,
        "project_root_hash": project_root_hash
    }


class OSFileLock:
    def __init__(self, lock_path: str) -> None:
        self.lock_path = os.path.abspath(lock_path)
        self.file_handle: Any = None
        self.locked = False
        self.owner_pid = os.getpid()
        try:
            import psutil
            self.owner_create_time: float | None = psutil.Process(self.owner_pid).create_time()
        except Exception:
            self.owner_create_time = None
        import uuid
        self.runtime_instance_id = uuid.uuid4().hex

    @property
    def is_held(self) -> bool:
        if os.environ.get("AIWF_DISABLE_FILE_LOCKS") == "1" and "PYTEST_CURRENT_TEST" in os.environ:
            return True
        return self.locked

    def acquire(self) -> bool:
        if os.environ.get("AIWF_DISABLE_FILE_LOCKS") == "1" and "PYTEST_CURRENT_TEST" in os.environ:
            return True
        try:
            os.makedirs(os.path.dirname(self.lock_path), exist_ok=True)
            self.file_handle = open(self.lock_path, "w")

            try:
                import fcntl
                flock = getattr(fcntl, "flock", None)
                lock_ex = getattr(fcntl, "LOCK_EX", 2)
                lock_nb = getattr(fcntl, "LOCK_NB", 4)
                if callable(flock):
                    flock(self.file_handle, lock_ex | lock_nb)
            except (ImportError, AttributeError):
                import msvcrt
                self.file_handle.seek(0)
                msvcrt.locking(self.file_handle.fileno(), msvcrt.LK_NBLCK, 1)

            self.locked = True
            return True
        except (ImportError, OSError):
            if self.file_handle:
                try:
                    self.file_handle.close()
                except Exception:
                    pass
                self.file_handle = None
            return False

    def release(self) -> None:
        if os.environ.get("AIWF_DISABLE_FILE_LOCKS") == "1" and "PYTEST_CURRENT_TEST" in os.environ:
            return

        if not self.locked or not self.file_handle:
            return

        current_pid = os.getpid()
        try:
            import psutil
            current_create_time: float | None = psutil.Process(current_pid).create_time()
        except Exception:
            current_create_time = None

        if current_pid != self.owner_pid:
            return
        if self.owner_create_time is not None and current_create_time is not None:
            if abs(current_create_time - self.owner_create_time) > 1.0:
                return

        try:
            try:
                import fcntl
                flock = getattr(fcntl, "flock", None)
                lock_un = getattr(fcntl, "LOCK_UN", 8)
                if callable(flock):
                    flock(self.file_handle, lock_un)
            except (ImportError, AttributeError):
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
        self.locked = False


DEFAULT_CLIENT_POLICY: dict[str, Any] = {
    "max_interactive_clients": 1,
    "detach_previous_on_new_attach": True,
    "preserve_background_workers": True
}

DEFAULT_RESOURCE_LIMITS: dict[str, Any] = {
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

DEFAULT_TEST_EXECUTION: dict[str, Any] = {
    "max_parallel_pytest_processes": 1,
    "max_pytest_workers": 2,
    "default_mode": "affected",
    "allow_full_suite_concurrency": False,
    "timeout_seconds": 1800,
    "retry_limit": 2,
    "kill_process_tree_on_timeout": True,
    "cooldown_seconds": 5
}

DEFAULT_SPAWN_LIMITS: dict[str, Any] = {
    "max_total_subagents": 8,
    "max_subagents_per_work_item": 4,
    "max_spawn_per_minute": 10,
    "max_pending_spawns": 5,
    "max_spawn_depth": 1,
    "allow_subagent_spawn_subagent": False,
    "max_failed_spawn_retries": 2
}


def load_config_section(section_name: str, default_val: dict[str, Any]) -> dict[str, Any]:
    config_path = os.path.join(".agents", "workflow.config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data_map = cast(dict[str, Any], data)
                if section_name in data_map:
                    res = data_map[section_name]
                    if isinstance(res, dict):
                        return cast(dict[str, Any], res)
        except Exception:
            pass
    return default_val


DEFAULT_RUNTIME_POLICY: dict[str, Any] = {
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
    sections = ["resource_limits", "scheduler", "pytest"]
    for s in sections:
        if s not in policy or not isinstance(policy[s], dict):
            return False, f"Missing or invalid section: '{s}'."

    rl_keys: dict[str, type | tuple[type, ...]] = {
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

    rl = cast(dict[str, Any], policy["resource_limits"])
    for k, t in rl_keys.items():
        if k not in rl:
            return False, f"Missing key in resource_limits: '{k}'."
        if not isinstance(rl[k], t):
            return False, f"Invalid type for resource_limits.{k}: expected {t}, got {type(rl[k])}."

    sch_keys: dict[str, type] = {
        "adaptive_concurrency": bool,
        "pause_on_high_cpu": bool,
        "pause_on_high_memory": bool
    }
    sch = cast(dict[str, Any], policy["scheduler"])
    for k, t in sch_keys.items():
        if k not in sch:
            return False, f"Missing key in scheduler: '{k}'."
        if not isinstance(sch[k], t):
            return False, f"Invalid type for scheduler.{k}: expected {t}, got {type(sch[k])}."

    py_keys: dict[str, type] = {
        "default_mode": str,
        "run_full_suite_only_at_final_review": bool,
        "deduplicate_requests": bool
    }
    py = cast(dict[str, Any], policy["pytest"])
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

    if not isinstance(policy, dict):
        if validate:
            raise ValueError("runtime-policy.json must be a JSON object.")
        return DEFAULT_RUNTIME_POLICY

    policy_dict = cast(dict[str, Any], policy)
    if validate:
        ok, err = validate_runtime_policy(policy_dict)
        if not ok:
            raise ValueError(f"Invalid runtime-policy.json schema: {err}")

    return policy_dict


__all__ = [
    "SessionLock",
    "load_workflow_config",
    "load_guardrails_summary",
    "load_approval_state",
    "load_dashboard_state",
    "get_project_identity",
    "OSFileLock",
    "DEFAULT_CLIENT_POLICY",
    "DEFAULT_RESOURCE_LIMITS",
    "DEFAULT_TEST_EXECUTION",
    "DEFAULT_SPAWN_LIMITS",
    "load_config_section",
    "DEFAULT_RUNTIME_POLICY",
    "get_runtime_policy_path",
    "validate_runtime_policy",
    "write_runtime_policy",
    "load_runtime_policy",
]
