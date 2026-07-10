# approval_gate.py
import os
import json
import time
from session import load_session, save_session_atomic

PENDING_CHOICE_FILE = os.path.join(".agents", "runtime", "pending-choice.json")
CHOICE_RESPONSE_FILE = os.path.join(".agents", "runtime", "choice-response.json")

def create_choice(choice_id: str, title: str, desc: str, options: list, choice_type: str = "choice") -> dict:
    os.makedirs(os.path.dirname(PENDING_CHOICE_FILE), exist_ok=True)
    
    choice_data = {
        "type": choice_type,
        "id": choice_id,
        "title": title,
        "description": desc,
        "options": options,
        "required": True,
        "allow_cancel": True
    }
    
    with open(PENDING_CHOICE_FILE, "w", encoding="utf-8") as f:
        json.dump(choice_data, f, indent=2, ensure_ascii=False)
        
    # Clear any previous response
    if os.path.exists(CHOICE_RESPONSE_FILE):
        try:
            os.remove(CHOICE_RESPONSE_FILE)
        except Exception:
            pass
            
    return {
        "status": "success",
        "command": "choice create",
        "summary": f"Choice '{choice_id}' created successfully.",
        "warnings": [],
        "files_read": [],
        "files_written": [PENDING_CHOICE_FILE],
        "next_skill": None
    }

def read_choice(choice_id: str) -> dict:
    if os.path.exists(CHOICE_RESPONSE_FILE):
        try:
            with open(CHOICE_RESPONSE_FILE, "r", encoding="utf-8") as f:
                res = json.load(f)
            if res.get("id") == choice_id:
                return {
                    "status": "success",
                    "command": "choice read",
                    "summary": f"Choice resolved: {res.get('selected_id') or res.get('status')}",
                    "warnings": [],
                    "files_read": [CHOICE_RESPONSE_FILE],
                    "files_written": [],
                    "choice": res
                }
        except Exception:
            pass
            
    return {
        "status": "failure",
        "command": "choice read",
        "summary": f"Choice '{choice_id}' is not resolved yet.",
        "warnings": ["Response file missing or corrupt"],
        "files_read": [],
        "files_written": [],
        "choice": None
    }

def clear_choice(choice_id: str) -> dict:
    files_deleted = []
    for path in [PENDING_CHOICE_FILE, CHOICE_RESPONSE_FILE]:
        if os.path.exists(path):
            try:
                os.remove(path)
                files_deleted.append(path)
            except Exception:
                pass
    return {
        "status": "success",
        "command": "choice clear",
        "summary": f"Cleared choice '{choice_id}'.",
        "warnings": [],
        "files_read": [],
        "files_written": files_deleted,
        "next_skill": None
    }
