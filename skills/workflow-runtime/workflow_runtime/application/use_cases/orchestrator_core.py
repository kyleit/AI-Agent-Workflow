from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any

from workflow_runtime.application.verification.test_enforcer import (
    patch_subprocess)
from workflow_runtime.infrastructure.session.state_store import (
    get_active_work_item_id)

patch_subprocess()

STATE_DIR = os.path.join(".agents", "state", "orchestrator")
CP_DIR = os.path.join(STATE_DIR, "checkpoints")
ART_DIR = os.path.join("artifacts", "autonomous-orchestrator")

os.makedirs(CP_DIR, exist_ok=True)
os.makedirs(ART_DIR, exist_ok=True)

AUTH_PATH = os.path.join(".agents", "state", "authorization.json")
AUTH_ORCH_PATH = os.path.join(STATE_DIR, "authorization.json")


def resolve_state_dir(work_item_id: str | None = None) -> str:
    wid = work_item_id or get_active_work_item_id()
    if wid:
        return os.path.join(".agents", "state", "work-items", wid, "orchestrator")
    return os.path.join(".agents", "state", "orchestrator")


def resolve_cp_dir(work_item_id: str | None = None) -> str:
    return os.path.join(resolve_state_dir(work_item_id), "checkpoints")


def resolve_auth_path(work_item_id: str | None = None) -> str:
    wid = work_item_id or get_active_work_item_id()
    if wid:
        return os.path.join(".agents", "state", "work-items", wid, "authorization.json")
    return os.path.join(".agents", "state", "authorization.json")


def resolve_auth_orch_path(work_item_id: str | None = None) -> str:
    return os.path.join(resolve_state_dir(work_item_id), "authorization.json")


def create_authorization(work_item_id: str) -> dict[str, Any]:
    auth_data: dict[str, Any] = {
        "authorization_id": f"AUTH-{int(time.time())}",
        "authorization_scope": "project-delivery",
        "authorization_status": "active",
        "mode": "autonomous_delivery",
        "project_id": "ai-skill-framework",
        "work_item_id": work_item_id,
        "workflow_scope": [
            "discovery",
            "planning",
            "blueprint",
            "architecture_validation",
            "implementation",
            "debug",
            "test",
            "verification"
        ],
        "allowed_paths": [
            "docs/brainstorming/",
            "docs/plans/",
            "docs/blueprints/",
            "docs/debug/",
            "docs/verification/",
            "artifacts/autonomous-orchestrator/"
        ],
        "forbidden_paths": [
            "skills/environment-bootstrap/",
            "skills/orchestrator/"
        ],
        "git_branch": "main",
        "allow_file_create": True,
        "allow_file_modify": True,
        "allow_test_modify": True,
        "allow_runtime_state_modify": True,
        "allow_retry": True,
        "allow_reassignment": True,
        "allow_parallel_execution": True,
        "allow_commit": False,
        "allow_push": False,
        "allow_merge": False,
        "allow_tag": False,
        "allow_release": False,
        "allow_deploy": False,
        "expires_when": "work_item_terminal",
        "created_at": datetime.now().astimezone().isoformat(),
        "terminated_at": None
    }

    auth_path = resolve_auth_path(work_item_id)
    auth_orch_path = resolve_auth_orch_path(work_item_id)
    os.makedirs(os.path.dirname(auth_path), exist_ok=True)
    os.makedirs(os.path.dirname(auth_orch_path), exist_ok=True)
    os.makedirs(ART_DIR, exist_ok=True)

    with open(auth_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)
    with open(auth_orch_path, "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)

    with open(os.path.join(ART_DIR, "authorization.json"), "w", encoding="utf-8") as f:
        json.dump(auth_data, f, indent=2)

    return auth_data


__all__ = [
    "STATE_DIR",
    "CP_DIR",
    "ART_DIR",
    "AUTH_PATH",
    "AUTH_ORCH_PATH",
    "resolve_state_dir",
    "resolve_cp_dir",
    "resolve_auth_path",
    "resolve_auth_orch_path",
    "create_authorization",
]
