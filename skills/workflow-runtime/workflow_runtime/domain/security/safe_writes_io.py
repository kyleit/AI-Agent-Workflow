# safe_multi_agent_writes.py
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from typing import Any, cast

STATE_DIR = os.path.join(".agents", "state")

def ensure_state_dir() -> None:
    os.makedirs(STATE_DIR, exist_ok=True)

def read_json_safe(path: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    def_val: dict[str, Any] = default if default is not None else {}
    if not os.path.exists(path):
        return def_val
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw: Any = json.load(f)
            if isinstance(raw, dict):
                return cast(dict[str, Any], raw)
            return def_val
    except Exception:
        return def_val

def write_json_atomic(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(path))
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, path)
    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def calculate_hash(content: str) -> str:
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def calculate_file_hash(path: str) -> str:
    if not os.path.exists(path):
        return ""
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()