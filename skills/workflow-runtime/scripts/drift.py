# drift.py
import os
import sys

# Ensure sibling imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from validator import get_git_info, get_version_info

def check_context_drift(session: dict) -> tuple[bool, str]:
    if not session:
        return False, "No active session"
        
    # Check Git branch drift
    git_info = get_git_info()
    saved_git = session.get("git", {})
    if git_info["is_git_repository"] or saved_git.get("is_git_repository"):
        if git_info["branch"] != saved_git.get("branch"):
            return True, f"Branch drifted: active is '{git_info['branch']}', saved is '{saved_git.get('branch')}'"
            
    # Check project version drift
    ver_info = get_version_info()
    saved_ver = session.get("version", {})
    if ver_info["version"] != saved_ver.get("version"):
        return True, f"Project version drifted: active is '{ver_info['version']}', saved is '{saved_ver.get('version')}'"
        
    return False, ""
