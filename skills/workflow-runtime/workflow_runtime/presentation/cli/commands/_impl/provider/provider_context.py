from __future__ import annotations

from typing import Any

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from workflow_runtime.infrastructure.session.state_sync import \
    write_json_atomic


def _is_aiwf_project_root(path: str) -> bool:
    return (
        os.path.exists(os.path.join(path, ".agents", "AI_RULES.md"))
        or os.path.exists(os.path.join(path, "AI_RULES.md"))
    )


def _resolve_aiwf_project_root() -> str:
    cwd = os.path.abspath(".")
    if _is_aiwf_project_root(cwd):
        return cwd
    probe = Path(__file__).resolve()
    for parent in probe.parents:
        if parent.name == ".agents":
            return str(parent.parent)
        if parent.name == "public_export":
            return str(parent.parent)
        if _is_aiwf_project_root(str(parent)):
            return str(parent)
    try:
        from workflow_runtime.application.workflow import \
            aiwf_registry  # noqa: PLC0415
        registry = aiwf_registry.load_registry()
        for project in registry.get("projects", []):
            path = str(project.get("path") or "")
            if path and os.path.exists(path) and _is_aiwf_project_root(path):
                return os.path.abspath(path)
    except Exception:
        pass
    return cwd


def has_global_telegram_token() -> bool:
    cfg_path = os.path.expanduser("~/.aiwf/.env.telegram-notify")
    if not os.path.exists(cfg_path):
        return False
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            for line in f:
                if (
                    line.strip().startswith("TELEGRAM_BOT_TOKEN=")
                    and line.split("=", 1)[1].strip().strip('"').strip("'")
                ):
                    return True
    except Exception:
        return False
    return False


def refresh_git_state_cache() -> dict[str, object]:
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
    )
    status = subprocess.run(
        ["git", "status", "--short"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
    )
    data: dict[str, Any] = {
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "ok": branch.returncode == 0 and status.returncode == 0,
        "branch": branch.stdout.strip(),
        "status_short": status.stdout.splitlines(),
        "stderr": (branch.stderr or status.stderr).strip(),
        "source": "aiwf config",
    }
    write_json_atomic(os.path.join(".agents", "state", "git.json"), data)
    return data


def get_current_project_context() -> dict[str, object]:
    project_root = _resolve_aiwf_project_root()
    context: dict[str, object] = {
        "name": os.path.basename(project_root),
        "path": ".",
        "absolute_path": project_root,
        "registered": False,
        "registry_id": None,
        "telegram_chat_id": None,
    }
    for manifest_path in (
        os.path.join(project_root, ".agents", "MANIFEST.json"),
        os.path.join(project_root, "MANIFEST.json"),
    ):
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                context["name"] = manifest.get("name") or context["name"]
                break
            except Exception:
                pass
    try:
        from workflow_runtime.application.workflow import \
            aiwf_registry  # noqa: PLC0415
        registry = aiwf_registry.load_registry()
        current = aiwf_registry.normalize_path(project_root)
        for project in registry.get("projects", []):
            if aiwf_registry.normalize_path(project.get("path", ".")) == current:
                context["registered"] = True
                context["registry_id"] = project.get("id")
                context["telegram_chat_id"] = project.get("telegram_chat_id")
                context["registry_status"] = project.get("status")
                break
    except Exception as e:
        context["registry_error"] = str(e)
    return context


def print_project_context() -> None:
    ctx = get_current_project_context()
    print(f"[PROJECT]: {ctx.get('name')} ({ctx.get('path')})")
    suffix = f", telegram_chat_id={ctx.get('telegram_chat_id')}" if ctx.get("telegram_chat_id") else ""
    print(f"[PROJECT]: registered={'yes' if ctx.get('registered') else 'no'}{suffix}")


def ensure_project_registered_from_config() -> dict[str, object]:
    try:
        from workflow_runtime.application.workflow import \
            aiwf_registry  # noqa: PLC0415
        registry = aiwf_registry.load_registry()
        current = str(aiwf_registry.normalize_path("."))
        for project in registry.get("projects", []):
            if str(aiwf_registry.normalize_path(project.get("path", ""))) == current:
                return {"status": "already_registered", "path": current}
        result = aiwf_registry.register_project(".", force=True, source="config")
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


def refresh_initialize_dependencies() -> dict[str, object]:
    from workflow_runtime.application.dependency.dependency_resolver import (  # noqa: PLC0415
        parse_requirements, resolve_requirements)
    skill = "initialize-workflow"
    reqs = parse_requirements(skill)
    ctx = resolve_requirements(skill, reqs)
    return {
        "skill": skill,
        "resolved": len(ctx.resolved),
        "warnings": ctx.warnings,
        "path": ".agents/state/runtime/dependencies.json",
    }


def process_runtime_bus_once(*_args: object, **_kwargs: object) -> None:
    """Stub: process_runtime_bus_once moved or not yet implemented."""
