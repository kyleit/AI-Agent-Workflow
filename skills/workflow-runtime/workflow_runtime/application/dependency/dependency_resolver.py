from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, cast

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import workflow_runtime.application.dependency.dependency_scanner as scanner
from workflow_runtime.application.dependency.dependency_models import (
    DependencyResult, MissingRequiredDependencyError, ResolvedRuntimeContext,
    ValidationResult)
from workflow_runtime.application.dependency.environment_inspector import (
    check_workspace_scan_allowed, read_environment_snapshot)
import workflow_runtime.application.dependency.runtime_context_loaders as p2
from workflow_runtime.application.dependency.runtime_context_loaders import (
    load_memory_cached, load_rag_cached)

SUPPORTED_KEYS = {
    "rules", "state", "approvals", "git", "memory", "rag",
    "workspace_scan", "environment", "version", "provider", "usage",
}

DEPRECATED_KEYS = {
    "transcript_sync": "usage",
    "provider_usage": "provider",
}

SUPPORTED_MODES = {"required", "cached", "lazy", "optional", "none"}

SAFETY_KEYS = {"rules", "state"}

WORKSPACE_SCAN_ALLOWED_SKILLS = {
    "project-memory-bootstrap",
    "project-memory-update",
    "project-discovery",
}

USAGE_REQUIRED_ALLOWED_SKILLS = {
    "context-reporter",
    "analytics-agent",
    "budget-controller",
}

VERSION_REQUIRED_ALLOWED_SKILLS = {
    "implementation-to-release",
    "release-manager",
}

_STATE_DIR = os.path.join(".agents", "state")
_RUNTIME_STATE_DIR = os.path.join(_STATE_DIR, "runtime")
DEPENDENCIES_LOG_PATH = os.path.join(_RUNTIME_STATE_DIR, "dependencies.json")
ENVIRONMENT_SNAPSHOT_PATH = os.path.join(_STATE_DIR, "environment.json")
CONTEXT_PATH = os.path.join(_STATE_DIR, "context.json")
APPROVALS_PATH = os.path.join(_STATE_DIR, "approvals.json")
DASHBOARD_PATH = os.path.join(_STATE_DIR, "dashboard.json")

SAFE_MINIMAL_FALLBACK = {
    "rules": "required",
    "state": "required",
    "approvals": "optional",
    "git": "cached",
    "memory": "none",
    "rag": "none",
    "workspace_scan": "none",
    "environment": "none",
    "version": "none",
    "provider": "none",
    "usage": "none",
}


def _write_json_atomic(file_path: str, data: Any) -> None:
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, file_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _read_json_safe(file_path: str) -> dict[str, Any]:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def parse_requirements(skill_name: str) -> dict[str, Any]:
    find_fn: Any = getattr(scanner, "_find_skill_md", None)
    sp_raw: Any = find_fn(skill_name) if callable(find_fn) else None
    skill_path = str(sp_raw) if sp_raw else ""
    if not skill_path or not os.path.exists(skill_path):
        return {}

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    frontmatter = parts[1]
    requirements: dict[str, str] = {}
    in_requirements = False

    for line in frontmatter.splitlines():
        stripped = line.rstrip()

        if stripped.strip() == "runtime_requirements:":
            in_requirements = True
            continue

        if in_requirements:
            if stripped and not stripped.startswith(" ") and not stripped.startswith("	"):
                if ":" in stripped:
                    break
            if stripped.startswith("  ") or stripped.startswith("	"):
                colon_idx = stripped.find(":")
                if colon_idx > 0:
                    key = stripped[:colon_idx].strip()
                    value = stripped[colon_idx + 1:].strip()
                    if key and value:
                        requirements[key] = value

    return requirements


def validate_requirements(skill_name: str, requirements: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    for key, mode in requirements.items():
        if key in DEPRECATED_KEYS:
            new_key = DEPRECATED_KEYS[key]
            warnings.append(
                f"Key '{key}' is deprecated. Run 'deps fix' to migrate to '{new_key}'."
            )
            continue

        if key not in SUPPORTED_KEYS:
            errors.append(
                f"Invalid key '{key}' in runtime_requirements. "
                f"Valid keys: {sorted(SUPPORTED_KEYS)}"
            )
            continue

        if mode not in SUPPORTED_MODES:
            errors.append(
                f"Invalid mode '{mode}' for key '{key}'. "
                f"Valid modes: {sorted(SUPPORTED_MODES)}"
            )
            continue

        if key in SAFETY_KEYS and mode in ("lazy", "optional", "none"):
            errors.append(
                f"SafetyKeyViolationError: '{key}' cannot be '{mode}'. "
                f"Safety keys must be 'required' (rules, state, approvals are mandatory guardrails)."
            )

        if key == "workspace_scan" and mode == "required":
            if skill_name not in WORKSPACE_SCAN_ALLOWED_SKILLS:
                errors.append(
                    f"WorkspaceScanBlockedError: skill '{skill_name}' cannot set workspace_scan: required. "
                    f"Only allowed for: {sorted(WORKSPACE_SCAN_ALLOWED_SKILLS)}"
                )

        if key == "usage" and mode == "required":
            if skill_name not in USAGE_REQUIRED_ALLOWED_SKILLS:
                warnings.append(
                    f"usage: required is restricted. Skill '{skill_name}' should use 'cached' or 'lazy' instead. "
                    f"Allowed for: {sorted(USAGE_REQUIRED_ALLOWED_SKILLS)}"
                )

        if key == "version" and mode == "required":
            if skill_name not in VERSION_REQUIRED_ALLOWED_SKILLS:
                warnings.append(
                    f"version: required is restricted. Skill '{skill_name}' should use 'cached' instead. "
                    f"Allowed for: {sorted(VERSION_REQUIRED_ALLOWED_SKILLS)}"
                )

    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


def resolve_requirements(skill_name: str, requirements: dict[str, Any]) -> ResolvedRuntimeContext:
    if not requirements:
        requirements = dict(SAFE_MINIMAL_FALLBACK)

    validation = validate_requirements(skill_name, requirements)
    if not validation.ok:
        for err in validation.errors:
            print(f"[DEPS ERROR] {err}", file=sys.stderr)
        raise SystemExit(1)

    resolved: dict[str, DependencyResult] = {}
    missing_required: list[str] = []
    warnings: list[str] = list(validation.warnings)

    for key, mode in requirements.items():
        if key in DEPRECATED_KEYS:
            continue

        result = _resolve_single(skill_name, key, str(mode))
        resolved[key] = result

        if mode == "required" and result.status in ("missing", "blocked"):
            missing_required.append(key)
            print(
                f"[DEPS BLOCK] Required dependency '{key}' cannot be resolved for skill '{skill_name}'. "
                f"Status: {result.status}. Source: {result.source}",
                file=sys.stderr,
            )
        elif result.status == "stale":
            warnings.append(f"Dependency '{key}' is stale. {result.source}")
        elif result.status == "missing" and mode in ("cached", "lazy", "optional"):
            warnings.append(f"Dependency '{key}' is missing but mode='{mode}' so execution continues.")

    if missing_required:
        raise MissingRequiredDependencyError(
            f"Cannot run skill '{skill_name}': missing required dependencies: {missing_required}"
        )

    ctx = ResolvedRuntimeContext(
        skill=skill_name,
        resolved_at=datetime.now(timezone.utc).isoformat(),
        requirements=requirements,
        resolved=resolved,
        missing_required=missing_required,
        warnings=warnings,
    )

    _write_json_atomic(DEPENDENCIES_LOG_PATH, {
        "skill": ctx.skill,
        "resolved_at": ctx.resolved_at,
        "requirements": requirements,
        "resolved": {
            k: {
                "name": v.name, "mode": v.mode, "status": v.status,
                "source": v.source, "action": v.action,
            }
            for k, v in ctx.resolved.items()
        },
        "missing_required": ctx.missing_required,
        "warnings": ctx.warnings,
    })

    return ctx


def _resolve_single(skill_name: str, key: str, mode: str) -> DependencyResult:
    if mode == "none":
        return DependencyResult(name=key, mode=mode, status="skipped", source="mode=none", action="ok")

    resolve_ver_fn: Any = getattr(p2, "_resolve_version_cached", None)
    resolve_prov_fn: Any = getattr(p2, "_resolve_provider_cached", None)
    resolve_usg_fn: Any = getattr(p2, "_resolve_usage_cached", None)

    resolver_map = {
        "rules":          _resolve_rules,
        "state":          _resolve_state,
        "approvals":      _resolve_approvals,
        "git":            _resolve_git_cached,
        "memory":         _resolve_memory,
        "rag":            _resolve_rag,
        "workspace_scan": _resolve_workspace_scan,
        "environment":    _resolve_environment_snapshot,
        "version":        resolve_ver_fn,
        "provider":       resolve_prov_fn,
        "usage":          resolve_usg_fn,
    }

    resolver_fn = resolver_map.get(key)
    if resolver_fn is None:
        return DependencyResult(name=key, mode=mode, status="skipped", source="unknown-key", action="warn_only")

    try:
        return resolver_fn(skill_name, mode)
    except Exception as e:
        return DependencyResult(name=key, mode=mode, status="missing", source=str(e), action="block" if mode == "required" else "warn_only")


def _resolve_rules(skill_name: str, mode: str) -> DependencyResult:
    rules_files = ["AI_RULES.md", os.path.join(".agents", "AGENTS.md")]
    loaded = [f for f in rules_files if os.path.exists(f)]
    if loaded:
        return DependencyResult(name="rules", mode=mode, status="loaded", source=", ".join(loaded), action="ok")
    return DependencyResult(name="rules", mode=mode, status="missing", source="AI_RULES.md not found", action="block")


def _resolve_state(skill_name: str, mode: str) -> DependencyResult:
    context = _read_json_safe(CONTEXT_PATH)
    if context:
        return DependencyResult(name="state", mode=mode, status="loaded", source=CONTEXT_PATH, action="ok", data=context)
    return DependencyResult(name="state", mode=mode, status="missing", source=CONTEXT_PATH, action="block")


def _resolve_approvals(skill_name: str, mode: str) -> DependencyResult:
    approvals = _read_json_safe(APPROVALS_PATH)
    if bool(approvals) and os.path.exists(APPROVALS_PATH):
        return DependencyResult(name="approvals", mode=mode, status="loaded", source=APPROVALS_PATH, action="ok", data=approvals)
    if mode == "optional":
        return DependencyResult(name="approvals", mode=mode, status="missing", source=APPROVALS_PATH, action="warn_only")
    return DependencyResult(name="approvals", mode=mode, status="missing", source=APPROVALS_PATH, action="block")


def _resolve_git_cached(skill_name: str, mode: str) -> DependencyResult:
    context = _read_json_safe(CONTEXT_PATH)
    git_data: dict[str, Any] = cast(dict[str, Any], context.get("git", {})) if isinstance(context.get("git"), dict) else {}
    if git_data:
        return DependencyResult(name="git", mode=mode, status="cached", source=CONTEXT_PATH, action="ok", data=git_data)
    try:
        import subprocess
        branch = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, timeout=3
        ).stdout.strip() or "unknown"
        is_repo = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=3
        ).stdout.strip() == "true"
        status_out = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, timeout=3
        ).stdout.strip()
        git_data = {
            "branch": branch,
            "is_git_repository": is_repo,
            "working_tree": "dirty" if status_out else "clean",
        }
        return DependencyResult(name="git", mode=mode, status="cached", source="git-cli (3 allowed commands)", action="ok", data=git_data)
    except Exception as e:
        return DependencyResult(name="git", mode=mode, status="missing", source=str(e), action="warn_only")


def _resolve_memory(skill_name: str, mode: str) -> DependencyResult:
    if mode == "cached":
        return load_memory_cached()
    if mode == "lazy":
        return DependencyResult(name="memory", mode=mode, status="deferred", source="lazy-load", action="defer")
    if mode == "optional":
        result = load_memory_cached()
        result.action = "warn_only"
        return result
    memory_skills = {"project-memory-bootstrap", "project-memory-update", "project-rag-search"}
    if skill_name not in memory_skills:
        return DependencyResult(
            name="memory", mode=mode, status="blocked",
            source=f"skill '{skill_name}' not allowed to load full memory",
            action="block"
        )
    return DependencyResult(name="memory", mode=mode, status="deferred", source="full-load-pending", action="defer")


def _resolve_rag(skill_name: str, mode: str) -> DependencyResult:
    if mode in ("cached", "optional"):
        return load_rag_cached()
    if mode == "lazy":
        return DependencyResult(name="rag", mode=mode, status="deferred", source="lazy-load", action="defer")
    rag_skills = {"project-rag-search"}
    if skill_name not in rag_skills:
        return DependencyResult(
            name="rag", mode=mode, status="blocked",
            source=f"skill '{skill_name}' not allowed to require RAG",
            action="block"
        )
    return DependencyResult(name="rag", mode=mode, status="deferred", source="rag-connect-pending", action="defer")


def _resolve_workspace_scan(skill_name: str, mode: str) -> DependencyResult:
    return check_workspace_scan_allowed(skill_name, mode)


def _resolve_environment_snapshot(skill_name: str, mode: str) -> DependencyResult:
    return read_environment_snapshot()


def compute_deps_fix_diff(skill_name: str) -> dict[str, Any] | None:
    """Compatibility entrypoint kept beside the canonical resolver API."""
    from workflow_runtime.application.dependency.environment_inspector import compute_deps_fix_diff as _compute
    return _compute(skill_name)


def generate_safe_requirements_template(skill_name: str) -> str:
    from workflow_runtime.application.dependency.environment_inspector import generate_safe_requirements_template as _generate
    return _generate(skill_name)


__all__ = [
    "SUPPORTED_KEYS",
    "DEPRECATED_KEYS",
    "SUPPORTED_MODES",
    "SAFETY_KEYS",
    "WORKSPACE_SCAN_ALLOWED_SKILLS",
    "USAGE_REQUIRED_ALLOWED_SKILLS",
    "VERSION_REQUIRED_ALLOWED_SKILLS",
    "DEPENDENCIES_LOG_PATH",
    "ENVIRONMENT_SNAPSHOT_PATH",
    "CONTEXT_PATH",
    "APPROVALS_PATH",
    "DASHBOARD_PATH",
    "SAFE_MINIMAL_FALLBACK",
    "parse_requirements",
    "validate_requirements",
    "resolve_requirements",
    "compute_deps_fix_diff",
    "generate_safe_requirements_template",
]
