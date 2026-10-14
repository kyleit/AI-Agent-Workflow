"""Pure lexical path boundary; filesystem containment belongs to the adapter."""

from __future__ import annotations

from .domain import RepoPath


def normalize_scope_path(value: str, platform: str) -> RepoPath:
    if platform not in {"windows", "win32", "posix", "linux", "darwin"}:
        raise ValueError("SCOPE_INVALID")
    return RepoPath(value, windows=platform in {"windows", "win32"})
