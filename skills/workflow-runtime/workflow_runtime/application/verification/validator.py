from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, cast

from workflow_runtime.domain.security.safe_writes_io import read_json_safe

_STATE_DIR = os.path.join(".agents", "state")
_CONTEXT_PATH = os.path.join(_STATE_DIR, "context.json")
_ENVIRONMENT_PATH = os.path.join(_STATE_DIR, "environment.json")

_GIT_ALLOWED = {
    "git rev-parse --is-inside-work-tree",
    "git branch --show-current",
    "git status --short",
}
_GIT_FORBIDDEN = {
    "git --version",
    "git describe --tags",
    "git remote -v",
    "git fetch",
    "git tag",
}


def detect_work_item_cached() -> dict[str, Any]:
    """
    Read current work item from .agents/state/context.json only.
    NEVER scans docs/ directories.
    """
    read_fn: Any = read_json_safe
    context: dict[str, Any] = cast(dict[str, Any], read_fn(_CONTEXT_PATH))

    work_item_raw = context.get("work_item")
    if isinstance(work_item_raw, dict):
        work_item = cast(dict[str, Any], work_item_raw)
        if work_item.get("id"):
            return work_item

    work_id = str(cast(Any, context.get("work_item_id")) or cast(Any, context.get("active_feature")) or "")
    work_type = str(cast(Any, context.get("work_item_type")) or "FEAT")
    work_title = str(cast(Any, context.get("work_item_title")) or "")

    if work_id:
        return {"type": work_type, "id": work_id, "title": work_title}

    return {"type": "None", "id": "None", "title": "None"}


def read_environment_snapshot() -> dict[str, Any]:
    """
    Read .agents/state/environment.json without running any CLI checks.
    """
    if not os.path.exists(_ENVIRONMENT_PATH):
        return {"status": "missing", "stale": False, "data": {}}

    try:
        with open(_ENVIRONMENT_PATH, "r", encoding="utf-8") as f:
            env_data = json.load(f)
    except Exception:
        return {"status": "missing", "stale": False, "data": {}}

    if not isinstance(env_data, dict):
        return {"status": "missing", "stale": False, "data": {}}

    env_dict = cast(dict[str, Any], env_data)
    updated_at_str = str(env_dict.get("updated_at", "") or "")
    stale = False
    if updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str)
            now = datetime.now(timezone.utc)
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            age_seconds = (now - updated_at).total_seconds()
            if age_seconds > 86400:
                stale = True
        except Exception:
            pass

    return {
        "status": "stale" if stale else "cached",
        "stale": stale,
        "data": env_dict,
    }


def validate_safe_path(path: str, workspace_root: str = ".") -> str:
    """
    Ensure the path resides strictly within the workspace root.
    """
    abs_root = os.path.abspath(workspace_root)
    abs_path = os.path.abspath(path)

    if ".." in path:
        if not abs_path.startswith(abs_root):
            raise PermissionError(f"Path escape detected: '{path}' resolves outside workspace.")

    if not abs_path.startswith(abs_root):
        raise PermissionError(f"Path '{path}' is outside the workspace root.")

    return abs_path


def has_absolute_paths(content: str) -> bool:
    """
    Check if the content contains local absolute filesystem paths.
    """
    unix_pattern = r"/(Users|Volumes|private|home|var)/[a-zA-Z0-9_./-]+"
    win_pattern = r"\b[A-Za-z]:\\[a-zA-Z0-9_./\\]+"

    if re.search(unix_pattern, content) or re.search(win_pattern, content):
        return True
    return False


def validate_artifact_placement(path: str, active_skill: str) -> bool:
    """
    Verify that files created by active skills are placed under docs/
    and path structure conforms to the active skill.
    """
    normalized_path = path.replace("\\", "/")

    if not (normalized_path.startswith("docs/") or normalized_path.startswith(".agents/")):
        return False

    if active_skill == "brainstorming":
        return normalized_path.startswith("docs/brainstorming/")

    if active_skill == "planning":
        return normalized_path.startswith("docs/plans/")

    if active_skill == "blueprint":
        return normalized_path.startswith("docs/blueprints/")

    if active_skill in ["quick-feature", "quick-fix"]:
        if "plan" in normalized_path:
            return normalized_path.startswith("docs/plans/")
        if "blueprint" in normalized_path or "design" in normalized_path:
            return normalized_path.startswith("docs/blueprints/")
        if "brainstorm" in normalized_path:
            return normalized_path.startswith("docs/brainstorming/")

    return True


__all__ = [
    "detect_work_item_cached",
    "read_environment_snapshot",
    "validate_safe_path",
    "has_absolute_paths",
    "validate_artifact_placement",
]
