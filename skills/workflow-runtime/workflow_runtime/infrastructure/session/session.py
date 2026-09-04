"""Backward-compatible re-exports for session module."""
from .session_io import (acquire_session_lock, get_default_authorization_state,
                         get_project_permission_config_path, get_session_path,
                         load_project_permissions, load_session,
                         migrate_session_schema, release_session_lock,
                         SESSION_FILE,
                         save_session_atomic, validate_permissions_data,
                         write_project_permissions_atomic)
from .session_lock import (OSFileLock, SessionLock, get_runtime_policy_path,
                           DEFAULT_RUNTIME_POLICY, load_runtime_policy, validate_runtime_policy,
                           write_runtime_policy)

__all__ = [
    "get_project_permission_config_path",
    "load_project_permissions",
    "write_project_permissions_atomic",
    "validate_permissions_data",
    "get_default_authorization_state",
    "get_session_path",
    "migrate_session_schema",
    "load_session",
    "save_session_atomic",
    "acquire_session_lock",
    "release_session_lock",
    "SessionLock",
    "OSFileLock",
    "SESSION_FILE",
    "load_runtime_policy",
    "get_runtime_policy_path",
    "validate_runtime_policy",
    "write_runtime_policy",
    "DEFAULT_RUNTIME_POLICY",
]
