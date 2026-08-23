# permission_mode.py
from datetime import datetime
from typing import Any


def check_permission(session: dict[str, Any], action: str) -> dict[str, Any]:
    mode = session.get("permission_mode", "sandbox")

    # Simple check: sandbox limits certain direct modifications
    if mode == "sandbox" and action in ["network", "system_execute"]:
        return {
            "status": "failure",
            "command": "permission check",
            "summary": f"Action '{action}' is blocked in sandbox mode.",
            "warnings": ["Require full_access mode"],
            "files_read": [".agents/.session.json"],
            "files_written": [],
            "allowed": False
        }

    return {
        "status": "success",
        "command": "permission check",
        "summary": f"Action '{action}' is permitted under mode '{mode}'.",
        "warnings": [],
        "files_read": [".agents/.session.json"],
        "files_written": [],
        "allowed": True
    }

def set_permission_mode(session: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode not in ["sandbox", "full_access"]:
        return {
            "status": "failure",
            "command": "permission set",
            "summary": f"Invalid permission mode '{mode}'.",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }

    session["permission_mode"] = mode
    session["permission_mode_selected_at"] = datetime.now().astimezone().isoformat()
    session["permission_mode_selected_by"] = "user"

    return {
        "status": "success",
        "command": "permission set",
        "summary": f"Permission mode successfully changed to '{mode}'.",
        "warnings": ["unrestricted mode warning" if mode == "full_access" else ""],
        "files_read": [],
        "files_written": [".agents/.session.json"]
    }
