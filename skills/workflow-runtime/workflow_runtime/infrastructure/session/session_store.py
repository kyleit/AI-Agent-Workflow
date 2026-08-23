from __future__ import annotations

from typing import Any, cast

from workflow_runtime.infrastructure.session import session as legacy_session
from workflow_runtime.infrastructure.session import session_lock


class SessionStore:
    """Clean DDD adapter over the legacy session.py flat module."""

    def __init__(self) -> None:
        pass

    def load(self) -> dict[str, Any]:
        return legacy_session.load_session()

    def save(self, data: dict[str, Any]) -> None:
        legacy_session.save_session_atomic(data)

    def write(self, data: dict[str, Any]) -> None:
        self.save(data)

    def get_path(self) -> str:
        return legacy_session.get_session_path()

    def load_permissions(self) -> dict[str, Any] | None:
        return legacy_session.load_project_permissions()

    def save_permissions(self, data: dict[str, Any]) -> None:
        legacy_session.write_project_permissions_atomic(data)

    def validate_permissions(self, data: dict[str, Any]) -> tuple[bool, str]:
        return legacy_session.validate_permissions_data(data)

    def authorize(self, mode: str) -> None:
        data = self.load()
        if "workspace_permission" in data:
            data["workspace_permission"] = mode
            self.save(data)

    def load_workflow_config(self) -> dict[str, Any]:
        fn: Any = getattr(session_lock, "load_workflow_config", None)
        raw: Any = fn() if callable(fn) else {}
        return cast(dict[str, Any], raw) if isinstance(raw, dict) else {}

    def load_guardrails_summary(self) -> dict[str, Any]:
        fn: Any = getattr(session_lock, "load_guardrails_summary", None)
        raw: Any = fn() if callable(fn) else {}
        return cast(dict[str, Any], raw) if isinstance(raw, dict) else {}

    def load_approval_state(self) -> dict[str, Any]:
        fn: Any = getattr(session_lock, "load_approval_state", None)
        raw: Any = fn() if callable(fn) else {}
        return cast(dict[str, Any], raw) if isinstance(raw, dict) else {}

    def load_dashboard_state(self) -> dict[str, Any]:
        fn: Any = getattr(session_lock, "load_dashboard_state", None)
        raw: Any = fn() if callable(fn) else {}
        return cast(dict[str, Any], raw) if isinstance(raw, dict) else {}

    def acquire_lock(self, timeout: float = 10.0) -> None:
        legacy_session.acquire_session_lock(timeout=timeout)

    def release_lock(self) -> None:
        legacy_session.release_session_lock()

    def lock_context(self, timeout: float = 10.0) -> Any:
        return legacy_session.SessionLock(timeout=timeout)

    def get_project_identity(self, project_path: str = ".") -> dict[str, Any]:
        fn: Any = getattr(session_lock, "get_project_identity", None)
        raw: Any = fn(project_path) if callable(fn) else {}
        return cast(dict[str, Any], raw) if isinstance(raw, dict) else {}


default_store = SessionStore()


def load_session() -> dict[str, Any]:
    return default_store.load()


def save_session(data: dict[str, Any]) -> None:
    default_store.save(data)


__all__ = [
    "SessionStore",
    "default_store",
    "load_session",
    "save_session",
]
