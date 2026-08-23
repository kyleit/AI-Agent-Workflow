# drift.py
import os
import sys
from typing import Any, cast

# Ensure sibling imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from workflow_runtime.shared.git_utils import get_git_info, get_version_info


def check_context_drift(session: dict[str, Any]) -> tuple[bool, str]:
    if not session:
        return False, "No active session"

    # Check Git branch drift
    git_info = get_git_info()
    saved_git: dict[str, Any] = cast(dict[str, Any], session.get("git", {})) if isinstance(session.get("git"), dict) else {}
    if git_info["is_git_repository"] and saved_git.get("is_git_repository"):
        if git_info["branch"] != saved_git.get("branch"):
            return True, f"Branch drifted: active is '{git_info['branch']}', saved is '{saved_git.get('branch')}'"

    # Check project version drift
    ver_info = get_version_info()
    saved_ver: dict[str, Any] = cast(dict[str, Any], session.get("version", {})) if isinstance(session.get("version"), dict) else {}
    if ver_info["version"] != saved_ver.get("version"):
        return True, f"Project version drifted: active is '{ver_info['version']}', saved is '{saved_ver.get('version')}'"

    return False, ""
