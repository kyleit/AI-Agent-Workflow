# permission_mode.py
import json
from session import load_session, save_session_atomic
from datetime import datetime

def check_permission(action: str) -> dict:
    session = load_session()
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

def set_permission_mode(mode: str) -> dict:
    if mode not in ["sandbox", "full_access"]:
        return {
            "status": "failure",
            "command": "permission set",
            "summary": f"Invalid permission mode '{mode}'.",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }
        
    session = load_session()
    session["permission_mode"] = mode
    session["permission_mode_selected_at"] = datetime.now().astimezone().isoformat()
    session["permission_mode_selected_by"] = "user"
    save_session_atomic(session)
    
    return {
        "status": "success",
        "command": "permission set",
        "summary": f"Permission mode successfully changed to '{mode}'.",
        "warnings": ["unrestricted mode warning" if mode == "full_access" else ""],
        "files_read": [],
        "files_written": [".agents/.session.json"]
    }
