# session.py
import os
import json
import uuid
from datetime import datetime

SESSION_FILE = os.path.join(".agents", ".session.json")
TMP_SESSION_FILE = SESSION_FILE + ".tmp"

def get_session_path() -> str:
    return os.path.abspath(SESSION_FILE)

def load_session() -> dict:
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_session_atomic(data: dict) -> None:
    # Ensure parent dir exists
    os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
    
    # Preserve conversation_id
    if "conversation_id" not in data or not data["conversation_id"]:
        existing = load_session()
        data["conversation_id"] = existing.get("conversation_id", str(uuid.uuid4()))
    
    # Update timestamp
    data["updated_at"] = datetime.now().astimezone().isoformat()
    
    # Write to tmp file
    with open(TMP_SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Atomic rename/replace
    if os.path.exists(SESSION_FILE):
        os.replace(TMP_SESSION_FILE, SESSION_FILE)
    else:
        os.rename(TMP_SESSION_FILE, SESSION_FILE)
