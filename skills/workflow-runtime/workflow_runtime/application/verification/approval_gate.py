# approval_gate.py
from __future__ import annotations

import json
import os
from typing import Any

PENDING_CHOICE_FILE = os.path.join(".agents", "runtime", "pending-choice.json")
CHOICE_RESPONSE_FILE = os.path.join(".agents", "runtime", "choice-response.json")


def create_choice(choice_id: str, title: str, desc: str, options: list[Any], choice_type: str = "choice") -> dict[str, Any]:
    os.makedirs(os.path.dirname(PENDING_CHOICE_FILE), exist_ok=True)

    choice_data: dict[str, Any] = {
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


def read_choice(choice_id: str) -> dict[str, Any]:
    if os.path.exists(CHOICE_RESPONSE_FILE):
        try:
            with open(CHOICE_RESPONSE_FILE, "r", encoding="utf-8") as f:
                res = json.load(f)
            from typing import cast as _cast
            res_dict = _cast(dict[str, Any], res) if isinstance(res, dict) else {}
            if res_dict.get("id") == choice_id:
                return {
                    "status": "success",
                    "command": "choice read",
                    "summary": f"Choice resolved: {res_dict.get('selected_id') or res_dict.get('status')}",
                    "warnings": [],
                    "files_read": [CHOICE_RESPONSE_FILE],
                    "files_written": [],
                    "choice": res_dict
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


def clear_choice(choice_id: str) -> dict[str, Any]:
    files_deleted: list[str] = []
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


__all__ = [
    "create_choice",
    "read_choice",
    "clear_choice",
]
