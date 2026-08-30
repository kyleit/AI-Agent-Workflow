# approval_gate.py
from __future__ import annotations

import json
import hashlib
import os
from typing import Any

PENDING_CHOICE_FILE = os.path.join(".agents", "runtime", "pending-choice.json")
CHOICE_RESPONSE_FILE = os.path.join(".agents", "runtime", "choice-response.json")


def _read_json(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            value = json.load(f)
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _choice_context() -> dict[str, str]:
    workflow = _read_json(os.path.join(".agents", "state", "workflow.json"))
    approvals = _read_json(os.path.join(".agents", "state", "approvals.json"))
    raw_work_item = workflow.get("active_workflow") or workflow.get("work_item")
    work_item = raw_work_item.get("id") if isinstance(raw_work_item, dict) else raw_work_item
    blueprint_data = approvals.get("blueprint")
    blueprint = blueprint_data.get("path") if isinstance(blueprint_data, dict) else ""
    blueprint_hash = ""
    if isinstance(blueprint, str) and os.path.isfile(blueprint):
        try:
            with open(blueprint, "rb") as f:
                blueprint_hash = hashlib.sha256(f.read()).hexdigest()
        except OSError:
            pass
    return {
        "workflow_id": str(work_item or ""),
        "blueprint": str(blueprint or ""),
        "blueprint_sha256": blueprint_hash,
    }


def create_choice(choice_id: str, title: str, desc: str, options: list[Any], choice_type: str = "choice") -> dict[str, Any]:
    os.makedirs(os.path.dirname(PENDING_CHOICE_FILE), exist_ok=True)

    choice_data: dict[str, Any] = {
        "type": choice_type,
        "id": choice_id,
        "title": title,
        "description": desc,
        "options": options,
        "required": True,
        "allow_cancel": True,
        "context": _choice_context(),
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
    pending = _read_json(PENDING_CHOICE_FILE)
    response = _read_json(CHOICE_RESPONSE_FILE)
    if pending.get("id") != choice_id:
        return {"status": "blocked", "command": "choice read", "choice": None,
                "blocking_findings": ["choice_stale"], "files_written": []}
    if not response:
        return {"status": "pending", "command": "choice read", "choice": None,
                "files_read": [PENDING_CHOICE_FILE], "files_written": []}
    if response.get("id") != choice_id:
        return {"status": "blocked", "command": "choice read", "choice": None,
                "blocking_findings": ["choice_stale"], "files_written": []}
    if response.get("context") != pending.get("context"):
        return {"status": "blocked", "command": "choice read", "choice": None,
                "blocking_findings": ["choice_context_mismatch"], "files_written": []}
    return {
        "status": "success",
        "command": "choice read",
        "summary": f"Choice resolved: {response.get('selected_id') or response.get('status')}",
        "warnings": [],
        "files_read": [PENDING_CHOICE_FILE, CHOICE_RESPONSE_FILE],
        "files_written": [],
        "choice": response,
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
