# artifact_writer.py
import os
import json

LOCKS_FILE = os.path.join(".agents", "runtime", "file-locks.json")

def load_locks() -> dict:
    if os.path.exists(LOCKS_FILE):
        try:
            with open(LOCKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_locks(locks: dict):
    os.makedirs(os.path.dirname(LOCKS_FILE), exist_ok=True)
    with open(LOCKS_FILE, "w", encoding="utf-8") as f:
        json.dump(locks, f, indent=2, ensure_ascii=False)

def acquire_file_lock(filepath: str, pid: int) -> bool:
    normalized = os.path.abspath(filepath)
    locks = load_locks()
    
    # Check if locked by another active process
    if normalized in locks and locks[normalized] != pid:
        return False
        
    locks[normalized] = pid
    save_locks(locks)
    return True

def release_file_lock(filepath: str, pid: int) -> bool:
    normalized = os.path.abspath(filepath)
    locks = load_locks()
    if normalized in locks and locks[normalized] == pid:
        del locks[normalized]
        save_locks(locks)
        return True
    return False

def write_artifact_safe(filepath: str, content: str, pid: int = 1) -> dict:
    # Check locks
    if not acquire_file_lock(filepath, pid):
        return {
            "status": "failure",
            "command": "write artifact",
            "summary": f"File {filepath} is locked by another active process.",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }
        
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        release_file_lock(filepath, pid)
        return {
            "status": "failure",
            "command": "write artifact",
            "summary": f"Failed to write file {filepath}: {e}",
            "warnings": [],
            "files_read": [],
            "files_written": []
        }
        
    release_file_lock(filepath, pid)
    return {
        "status": "success",
        "command": "write artifact",
        "summary": f"File {filepath} written successfully.",
        "warnings": [],
        "files_read": [],
        "files_written": [filepath]
    }
