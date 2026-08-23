"""
workflow_runtime/application/dependency/environment_inspector.py

Environment snapshot reader, doctor reporter, and guardrails summary loader.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, cast

import workflow_runtime.application.dependency.dependency_scanner as scanner
from workflow_runtime.application.dependency.dependency_models import (
    DependencyResult, DoctorReport, ValidationResult, WorkspaceScanBlockedError)

_STATE_DIR = os.path.join(".agents", "state")
ENVIRONMENT_SNAPSHOT_PATH = os.path.join(_STATE_DIR, "environment.json")
DEPRECATED_KEYS = {
    "transcript_sync": "usage",
    "provider_usage": "provider",
}
SAFETY_KEYS = {"rules", "state"}
WORKSPACE_SCAN_ALLOWED_SKILLS = {
    "project-memory-bootstrap",
    "project-memory-update",
    "project-discovery",
}


def _read_json_safe(file_path: str) -> dict[str, Any]:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def _sha256_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""


def read_environment_snapshot() -> DependencyResult:
    env_data = _read_json_safe(ENVIRONMENT_SNAPSHOT_PATH)
    if not env_data:
        return DependencyResult(
            name="environment", mode="cached", status="missing",
            source="environment.json not found",
            action="warn_only",
        )

    updated_at_str = str(env_data.get("updated_at", ""))
    if updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str)
            now = datetime.now(timezone.utc)
            if updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=timezone.utc)
            age_seconds = (now - updated_at).total_seconds()
            if age_seconds > 86400:
                return DependencyResult(
                    name="environment", mode="cached", status="stale",
                    source=ENVIRONMENT_SNAPSHOT_PATH,
                    action="warn_only",
                    data=env_data,
                )
        except Exception:
            pass

    return DependencyResult(
        name="environment", mode="cached", status="cached",
        source=ENVIRONMENT_SNAPSHOT_PATH,
        action="ok",
        data=env_data,
    )


def check_workspace_scan_allowed(skill_name: str, mode: str) -> DependencyResult:
    if mode == "none":
        return DependencyResult(name="workspace_scan", mode=mode, status="skipped", source="mode=none", action="ok")

    if mode == "required" and skill_name not in WORKSPACE_SCAN_ALLOWED_SKILLS:
        msg = (
            f"WorkspaceScanBlockedError: skill '{skill_name}' attempted workspace_scan: required. "
            f"Only allowed for: {sorted(WORKSPACE_SCAN_ALLOWED_SKILLS)}"
        )
        raise WorkspaceScanBlockedError(msg)

    if skill_name in WORKSPACE_SCAN_ALLOWED_SKILLS:
        return DependencyResult(name="workspace_scan", mode=mode, status="deferred", source="allowed-skill", action="defer")

    return DependencyResult(
        name="workspace_scan", mode=mode, status="skipped",
        source=f"skill '{skill_name}' not in WORKSPACE_SCAN_ALLOWED_SKILLS",
        action="warn_only",
    )


def load_guardrails_summary() -> dict[str, Any]:
    rules_path = "AI_RULES.md"
    agents_path = os.path.join(".agents", "AGENTS.md")

    runtime = _read_json_safe(os.path.join(_STATE_DIR, "runtime.json"))
    current_skill = str(runtime.get("current_skill", "initialize-workflow"))
    find_md_fn: Any = getattr(scanner, "_find_skill_md", None)
    skill_path_raw = find_md_fn(current_skill) or find_md_fn("initialize-workflow") or "" if callable(find_md_fn) else ""
    skill_path = str(skill_path_raw)

    return {
        "rules_loaded": os.path.exists(rules_path),
        "ai_rules_hash": _sha256_file(rules_path),
        "agents_hash": _sha256_file(agents_path),
        "active_skill_hash": _sha256_file(skill_path),
        "active_skill_path": skill_path,
        "policy_flags": {
            "approval_gate": True,
            "git_gate": True,
            "blueprint_gate": True,
            "release_gate": True,
            "testing_gate": True,
            "workspace_permission_gate": True,
        },
    }


def get_doctor_report(strict_mode: bool = False) -> DoctorReport:
    import workflow_runtime.application.dependency.dependency_resolver as dep_res

    find_all_fn: Any = getattr(scanner, "_find_all_skills", None)
    all_skills: list[tuple[str, str]] = cast(list[tuple[str, str]], find_all_fn()) if callable(find_all_fn) else []

    clean: list[str] = []
    warn: list[str] = []
    error: list[str] = []
    details: dict[str, ValidationResult] = {}

    parse_fn: Any = getattr(dep_res, "parse_requirements", None)
    val_fn: Any = getattr(dep_res, "validate_requirements", None)

    for skill_name, _skill_path in all_skills:
        reqs = cast(dict[str, Any], parse_fn(skill_name)) if callable(parse_fn) else {}
        if not reqs:
            result = ValidationResult(
                ok=not strict_mode,
                errors=[] if not strict_mode else [
                    f"Missing runtime_requirements in '{skill_name}/SKILL.md'. "
                    f"Run 'deps fix --skill {skill_name}' to add a safe template."
                ],
                warnings=[] if strict_mode else [
                    f"'{skill_name}' has no runtime_requirements. "
                    f"Applying safe_minimal fallback. Run 'deps fix --skill {skill_name}'."
                ],
            )
        else:
            result = cast(ValidationResult, val_fn(skill_name, reqs)) if callable(val_fn) else ValidationResult(ok=True, errors=[], warnings=[])

        details[skill_name] = result

        if not result.ok:
            error.append(skill_name)
        elif result.warnings:
            warn.append(skill_name)
        else:
            clean.append(skill_name)

    return DoctorReport(
        total_skills=len(all_skills),
        clean_skills=clean,
        warning_skills=warn,
        error_skills=error,
        details=details,
    )


def generate_safe_requirements_template(skill_name: str) -> str:
    _ = skill_name
    return """runtime_requirements:
  rules: required
  state: required
  approvals: optional
  git: cached
  memory: cached
  rag: cached
  workspace_scan: none
  environment: cached
  version: cached
  provider: optional
  usage: cached
"""


def compute_deps_fix_diff(skill_name: str) -> dict[str, Any] | None:
    import workflow_runtime.application.dependency.dependency_resolver as dep_res

    find_md_fn: Any = getattr(scanner, "_find_skill_md", None)
    sp_raw = find_md_fn(skill_name) if callable(find_md_fn) else None
    skill_path = str(sp_raw) if sp_raw else ""
    if not skill_path:
        return None

    parse_fn: Any = getattr(dep_res, "parse_requirements", None)
    reqs = cast(dict[str, Any], parse_fn(skill_name)) if callable(parse_fn) else {}
    changes: list[str] = []
    migration_needed = False
    template_needed = False

    if not reqs:
        template_needed = True
        changes.append("ADD runtime_requirements block (safe_minimal template)")
    else:
        for key in list(reqs.keys()):
            if key in DEPRECATED_KEYS:
                new_key = DEPRECATED_KEYS[key]
                changes.append(f"MIGRATE '{key}' -> '{new_key}'")
                migration_needed = True

        for key in SAFETY_KEYS:
            if reqs.get(key) in ("lazy", "optional", "none"):
                changes.append(f"FIX safety key '{key}': '{reqs[key]}' -> 'required'")

        if reqs.get("workspace_scan") == "required" and skill_name not in WORKSPACE_SCAN_ALLOWED_SKILLS:
            changes.append("FIX workspace_scan: required -> none (skill not in allowlist)")

    if not changes:
        return None

    return {
        "skill_name": skill_name,
        "skill_path": skill_path,
        "changes": changes,
        "template_needed": template_needed,
        "migration_needed": migration_needed,
        "proposed_template": generate_safe_requirements_template(skill_name) if template_needed else None,
    }


__all__ = [
    "read_environment_snapshot",
    "check_workspace_scan_allowed",
    "load_guardrails_summary",
    "get_doctor_report",
    "generate_safe_requirements_template",
    "compute_deps_fix_diff",
]
