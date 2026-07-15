# validator.py
"""
Validator for AIWF Runtime.
FEAT-050: Replaced live git/env CLI checks with cached JSON readers.
Only 3 git commands are allowed during initialize-workflow:
  - git rev-parse --is-inside-work-tree
  - git branch --show-current
  - git status --short
"""
from __future__ import annotations

import json
import os
import subprocess
import re
from datetime import datetime, timezone

_STATE_DIR = os.path.join(".agents", "state")
_CONTEXT_PATH = os.path.join(_STATE_DIR, "context.json")
_ENVIRONMENT_PATH = os.path.join(_STATE_DIR, "environment.json")

# Allowed git commands (whitelist — exactly 3)
_GIT_ALLOWED = {
    "git rev-parse --is-inside-work-tree",
    "git branch --show-current",
    "git status --short",
}
# Forbidden git commands (fast-fail)
_GIT_FORBIDDEN = {
    "git --version",
    "git describe --tags",
    "git remote -v",
    "git fetch",
    "git tag",
}


def _read_json_safe(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def get_git_info() -> dict:
    """
    Run exactly the 3 allowed git commands to detect current branch and status.
    git describe --tags is REMOVED per FEAT-050.
    """
    info = {
        "is_git_repository": False,
        "branch": "unknown",
        "working_tree": "clean",
        "default_branch": "main",
        "latest_tag": "",  # No longer populated — use detect_project_version_cached()
    }

    # Check git repository
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, check=True, timeout=5,
        )
        if "true" in res.stdout.strip():
            info["is_git_repository"] = True
    except (subprocess.SubprocessError, FileNotFoundError, subprocess.TimeoutExpired):
        return info

    if info["is_git_repository"]:
        # Get active branch
        try:
            res_branch = subprocess.run(
                ["git", "branch", "--show-current"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5,
            )
            info["branch"] = res_branch.stdout.strip() or "detached"
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        # Get git status
        try:
            res_status = subprocess.run(
                ["git", "status", "--short"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, timeout=5,
            )
            if res_status.stdout.strip():
                info["working_tree"] = "dirty"
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            pass

        # NOTE: git describe --tags is REMOVED per FEAT-050 blueprint.
        # Use detect_project_version_cached() for version info.

    return info


def get_version_info() -> dict:
    """
    Deprecated: scans manifest files. Use detect_project_version_cached() instead.
    Kept for backwards compatibility with existing callers — reads .agents/MANIFEST.json only.
    Does NOT run git describe --tags per FEAT-050.
    """
    return detect_project_version_cached()


def detect_project_version_cached() -> dict:
    """
    Read project version from .agents/state/context.json only.
    NEVER scans package.json, go.mod, pyproject.toml, Cargo.toml, or MANIFEST.json.
    NEVER runs git describe --tags.
    """
    context = _read_json_safe(_CONTEXT_PATH)
    version = context.get("project_version") or context.get("version")
    if version:
        return {"version": str(version), "source": "context.json"}

    # Fallback: read only .agents/MANIFEST.json (framework version)
    agents_manifest = os.path.join(".agents", "MANIFEST.json")
    if os.path.exists(agents_manifest):
        try:
            with open(agents_manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
                v = data.get("version")
                if v:
                    return {"version": str(v), "source": ".agents/MANIFEST.json"}
        except Exception:
            pass

    return {"version": "0.0.0", "source": "unknown"}


def detect_work_item_cached() -> dict:
    """
    Read current work item from .agents/state/context.json only.
    NEVER scans docs/ directories.
    """
    context = _read_json_safe(_CONTEXT_PATH)

    # Try direct work_item key first
    work_item = context.get("work_item")
    if isinstance(work_item, dict) and work_item.get("id"):
        return work_item

    # Try individual fields
    work_id = context.get("work_item_id") or context.get("active_feature")
    work_type = context.get("work_item_type", "FEAT")
    work_title = context.get("work_item_title", "")

    if work_id:
        return {"type": work_type, "id": work_id, "title": work_title}

    return {"type": "None", "id": "None", "title": "None"}


def read_environment_snapshot() -> dict:
    """
    Read .agents/state/environment.json without running any CLI checks.
    Returns:
      status: "cached" | "stale" | "missing"
      data: environment dict or {}
      stale: bool
    NEVER runs python --version, node --version, docker version, etc.
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

    # Check staleness (>24h)
    updated_at_str = env_data.get("updated_at", "")
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
        "data": env_data,
    }


def validate_safe_path(path: str, workspace_root: str = ".") -> str:
    """
    Ensure the path resides strictly within the workspace root.
    Throws PermissionError if path resolves outside the workspace.
    """
    abs_root = os.path.abspath(workspace_root)
    abs_path = os.path.abspath(path)
    
    # Check directory traversal escape
    if ".." in path:
        if not abs_path.startswith(abs_root):
            raise PermissionError(f"Path escape detected: '{path}' resolves outside workspace.")
            
    if not abs_path.startswith(abs_root):
        raise PermissionError(f"Path '{path}' is outside the workspace root.")
        
    return abs_path


def has_absolute_paths(content: str) -> bool:
    r"""
    Check if the content contains local absolute filesystem paths.
    Prohibits patterns like /Users/... or /Volumes/... or Windows equivalents C:\...
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
        return normalized_path.startswith("docs/designs/")
        
    if active_skill in ["quick-feature", "quick-fix"]:
        if "plan" in normalized_path:
            return normalized_path.startswith("docs/plans/")
        if "blueprint" in normalized_path or "design" in normalized_path:
            return normalized_path.startswith("docs/designs/")
        if "brainstorm" in normalized_path:
            return normalized_path.startswith("docs/brainstorming/")
            
    return True
