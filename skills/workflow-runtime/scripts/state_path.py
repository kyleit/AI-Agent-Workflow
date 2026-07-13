# state_path.py
"""
Canonical path resolver for AIWF split state directory structure.
No imports from other AIWF modules to avoid circular imports.
"""
import os
import json
from typing import Optional

# Environment variable override for state root (for testing)
_STATE_ROOT_ENV = "AIWF_STATE_ROOT"

# Sub-directory names within state root
STATE_SUBDIRS = [
    "project",
    "workflow",
    "runtime",
    "context",
    "recovery",
    "events",
]

# Canonical file names per sub-directory
STATE_FILES = {
    "project": "profile.json",
    "workflow": "workflow.json",
    "runtime": "runtime.json",
    "context": "context.json",
    "recovery": "recovery.json",
}


def get_state_root(workspace_root: Optional[str] = None) -> str:
    """
    Return the absolute path to the canonical state root.
    Priority: AIWF_STATE_ROOT env var > workspace_root arg > os.getcwd()
    """
    env_override = os.environ.get(_STATE_ROOT_ENV)
    if env_override:
        return os.path.abspath(env_override)

    base = workspace_root if workspace_root else os.getcwd()
    return os.path.abspath(os.path.join(base, ".agents", "state"))


def get_subdir(name: str, workspace_root: Optional[str] = None) -> str:
    """
    Return the absolute path to a named sub-directory within state root.
    Valid names: 'project', 'workflow', 'runtime', 'context', 'recovery', 'events'.
    """
    if name not in STATE_SUBDIRS:
        raise ValueError(
            f"Unknown state subdir '{name}'. Valid: {STATE_SUBDIRS}"
        )
    return os.path.join(get_state_root(workspace_root), name)


def get_state_file(name: str, workspace_root: Optional[str] = None) -> str:
    """
    Return the absolute path to a canonical state file (e.g. workflow/workflow.json).
    """
    if name not in STATE_FILES:
        raise ValueError(
            f"No canonical file for state category '{name}'. Valid: {list(STATE_FILES.keys())}"
        )
    subdir = get_subdir(name, workspace_root)
    return os.path.join(subdir, STATE_FILES[name])


def get_events_path(workspace_root: Optional[str] = None) -> str:
    """Return the absolute path to events/events.jsonl."""
    return os.path.join(get_subdir("events", workspace_root), "events.jsonl")


def get_dashboard_path(workspace_root: Optional[str] = None) -> str:
    """Return the absolute path to state root dashboard.json."""
    return os.path.join(get_state_root(workspace_root), "dashboard.json")


def get_legacy_session_path(workspace_root: Optional[str] = None) -> str:
    """Return the absolute path to the legacy .agents/.session.json."""
    base = workspace_root if workspace_root else os.getcwd()
    return os.path.abspath(os.path.join(base, ".agents", ".session.json"))


def get_backups_dir(workspace_root: Optional[str] = None) -> str:
    """Return the absolute path to the state backups directory."""
    return os.path.join(get_state_root(workspace_root), "backups")


def get_migration_report_path(workspace_root: Optional[str] = None) -> str:
    """Return the absolute path to the state migration report."""
    return os.path.join(
        get_subdir("recovery", workspace_root), "state-migration-report.json"
    )


def ensure_dirs(workspace_root: Optional[str] = None) -> list[str]:
    """
    Create all canonical sub-directories if they don't exist.
    Returns list of directories created.
    """
    created = []
    for name in STATE_SUBDIRS:
        path = get_subdir(name, workspace_root)
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            created.append(path)
    # Ensure backups dir exists too
    backups = get_backups_dir(workspace_root)
    if not os.path.exists(backups):
        os.makedirs(backups, exist_ok=True)
        created.append(backups)
    return created


def is_within_state_root(path: str, workspace_root: Optional[str] = None) -> bool:
    """
    Check if a given absolute path is within the state root.
    Used for security validation.
    """
    root = get_state_root(workspace_root)
    return os.path.abspath(path).startswith(root)


def validate_relative_path(path: str) -> str:
    """
    Validate that a file path is relative (not absolute, no traversal).
    Raises SecurityError if invalid.
    Returns the normalized relative path.
    """
    if os.path.isabs(path):
        raise SecurityError(
            f"Absolute path rejected: '{path}'. Only relative paths allowed."
        )
    normalized = os.path.normpath(path)
    if normalized.startswith(".."):
        raise SecurityError(
            f"Path traversal rejected: '{path}'. Paths must stay within workspace."
        )
    return normalized


class SecurityError(ValueError):
    """Raised when a path security violation is detected."""
    pass
