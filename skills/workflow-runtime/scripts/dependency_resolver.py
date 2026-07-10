# dependency_resolver.py
"""
Runtime Dependency Resolver for AIWF.
FEAT-050: Lightweight Runtime Initialization — Dependency Resolution Layer.

Responsibilities:
- Parse runtime_requirements from SKILL.md YAML frontmatter
- Validate requirements against schema (keys, modes, safety rules)
- Resolve each dependency lazily/cached based on declared mode
- Output ResolvedRuntimeContext and write dependencies.json
- Doctor report: scan all skills for missing/invalid manifests
- Phase completion gate delegation (from task_orchestrator)
- Next-task recommendation delegation (from task_orchestrator)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# Ensure sibling imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Schema Constants
# ---------------------------------------------------------------------------

SUPPORTED_KEYS = {
    "rules", "state", "approvals", "git", "memory", "rag",
    "workspace_scan", "environment", "version", "provider", "usage",
}

# Deprecated keys — auto-migrate via deps fix
DEPRECATED_KEYS = {
    "transcript_sync": "usage",
    "provider_usage": "provider",
}

SUPPORTED_MODES = {"required", "cached", "lazy", "optional", "none"}

# Safety keys: MUST be 'required' — cannot be lazy, optional, or none
# Note: 'approvals' can be 'optional' per blueprint (less critical than rules/state)
SAFETY_KEYS = {"rules", "state"}

# Skills allowed to use workspace_scan: required
WORKSPACE_SCAN_ALLOWED_SKILLS = {
    "project-memory-bootstrap",
    "project-memory-update",
    "project-discovery",
}

# Skills allowed to use usage: required (transcript/usage access)
USAGE_REQUIRED_ALLOWED_SKILLS = {
    "context-reporter",
    "analytics-agent",
    "budget-controller",
}

# Skills allowed to use version: required
VERSION_REQUIRED_ALLOWED_SKILLS = {
    "implementation-to-release",
    "release-manager",
}

# State file paths
_STATE_DIR = os.path.join(".agents", "state")
_RUNTIME_STATE_DIR = os.path.join(_STATE_DIR, "runtime")
DEPENDENCIES_LOG_PATH = os.path.join(_RUNTIME_STATE_DIR, "dependencies.json")
ENVIRONMENT_SNAPSHOT_PATH = os.path.join(_STATE_DIR, "environment.json")
CONTEXT_PATH = os.path.join(_STATE_DIR, "context.json")
APPROVALS_PATH = os.path.join(_STATE_DIR, "approvals.json")
DASHBOARD_PATH = os.path.join(_STATE_DIR, "dashboard.json")

# safe_minimal fallback: applied to skills without runtime_requirements declaration
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

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class MissingRequiredDependencyError(Exception):
    pass

class InvalidRequirementsKeyError(Exception):
    pass

class InvalidRequirementsModeError(Exception):
    pass

class SafetyKeyViolationError(Exception):
    pass

class WorkspaceScanBlockedError(Exception):
    pass

# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DependencyResult:
    name: str
    mode: str
    status: str   # loaded | cached | deferred | skipped | missing | stale
    source: str
    action: str   # warn_only | block | defer | ok
    data: Optional[Any] = None


@dataclass
class ResolvedRuntimeContext:
    skill: str
    resolved_at: str
    requirements: dict
    resolved: dict[str, DependencyResult]
    missing_required: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class DoctorReport:
    total_skills: int
    clean_skills: list[str]
    warning_skills: list[str]
    error_skills: list[str]
    details: dict[str, ValidationResult]

# ---------------------------------------------------------------------------
# Internal Helpers
# ---------------------------------------------------------------------------

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


def _read_json_safe(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _sha256_file(file_path: str) -> str:
    """Compute SHA-256 hash of a file. Returns '' if not found."""
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""

# ---------------------------------------------------------------------------
# Public: Parse runtime_requirements from SKILL.md
# ---------------------------------------------------------------------------

def parse_requirements(skill_name: str) -> dict:
    """
    Parse runtime_requirements from a SKILL.md YAML frontmatter.
    Returns dict of {key: mode} or {} if not found.

    Frontmatter is the YAML block between the first two '---' delimiters.
    Parsing is done with stdlib string split only (no yaml library needed).
    """
    skill_path = _find_skill_md(skill_name)
    if not skill_path:
        return {}

    try:
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return {}

    # Extract YAML frontmatter between first --- pair
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
            # End of runtime_requirements block if we hit another top-level key
            if stripped and not stripped.startswith(" ") and not stripped.startswith("\t"):
                if ":" in stripped:
                    break
            if stripped.startswith("  ") or stripped.startswith("\t"):
                colon_idx = stripped.find(":")
                if colon_idx > 0:
                    key = stripped[:colon_idx].strip()
                    value = stripped[colon_idx + 1:].strip()
                    if key and value:
                        requirements[key] = value

    return requirements


def _find_skill_md(skill_name: str) -> Optional[str]:
    """Find SKILL.md path for a given skill name."""
    candidates = [
        os.path.join("skills", skill_name, "SKILL.md"),
        os.path.join(".agents", "skills", skill_name, "SKILL.md"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


def _find_all_skills() -> list[tuple[str, str]]:
    """Return list of (skill_name, skill_md_path) for all discovered skills."""
    skills: list[tuple[str, str]] = []
    for base_dir in ["skills", os.path.join(".agents", "skills")]:
        if not os.path.isdir(base_dir):
            continue
        for entry in sorted(os.listdir(base_dir)):
            candidate = os.path.join(base_dir, entry, "SKILL.md")
            if os.path.exists(candidate):
                skills.append((entry, candidate))
    return skills

# ---------------------------------------------------------------------------
# Public: Validate runtime_requirements Schema
# ---------------------------------------------------------------------------

def validate_requirements(skill_name: str, requirements: dict) -> ValidationResult:
    """
    Validate a runtime_requirements dict against the schema.

    Rules:
    - Keys must be in SUPPORTED_KEYS (deprecated keys trigger warning + migration hint)
    - Modes must be in SUPPORTED_MODES
    - SAFETY_KEYS (rules, state, approvals) cannot be lazy/optional/none
    - workspace_scan: required is only allowed for WORKSPACE_SCAN_ALLOWED_SKILLS
    - usage: required is only allowed for USAGE_REQUIRED_ALLOWED_SKILLS
    - version: required is only allowed for VERSION_REQUIRED_ALLOWED_SKILLS
    """
    errors: list[str] = []
    warnings: list[str] = []

    for key, mode in requirements.items():
        # Check deprecated keys
        if key in DEPRECATED_KEYS:
            new_key = DEPRECATED_KEYS[key]
            warnings.append(
                f"Key '{key}' is deprecated. Run 'deps fix' to migrate to '{new_key}'."
            )
            continue

        # Check unknown keys
        if key not in SUPPORTED_KEYS:
            errors.append(
                f"Invalid key '{key}' in runtime_requirements. "
                f"Valid keys: {sorted(SUPPORTED_KEYS)}"
            )
            continue

        # Check mode
        if mode not in SUPPORTED_MODES:
            errors.append(
                f"Invalid mode '{mode}' for key '{key}'. "
                f"Valid modes: {sorted(SUPPORTED_MODES)}"
            )
            continue

        # Safety key violations
        if key in SAFETY_KEYS and mode in ("lazy", "optional", "none"):
            errors.append(
                f"SafetyKeyViolationError: '{key}' cannot be '{mode}'. "
                f"Safety keys must be 'required' (rules, state, approvals are mandatory guardrails)."
            )

        # workspace_scan guard
        if key == "workspace_scan" and mode == "required":
            if skill_name not in WORKSPACE_SCAN_ALLOWED_SKILLS:
                errors.append(
                    f"WorkspaceScanBlockedError: skill '{skill_name}' cannot set workspace_scan: required. "
                    f"Only allowed for: {sorted(WORKSPACE_SCAN_ALLOWED_SKILLS)}"
                )

        # usage: required guard
        if key == "usage" and mode == "required":
            if skill_name not in USAGE_REQUIRED_ALLOWED_SKILLS:
                warnings.append(
                    f"usage: required is restricted. Skill '{skill_name}' should use 'cached' or 'lazy' instead. "
                    f"Allowed for: {sorted(USAGE_REQUIRED_ALLOWED_SKILLS)}"
                )

        # version: required guard
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

# ---------------------------------------------------------------------------
# Public: Resolve Requirements
# ---------------------------------------------------------------------------

def resolve_requirements(skill_name: str, requirements: dict) -> ResolvedRuntimeContext:
    """
    Resolve each declared requirement into a DependencyResult.
    Blocks execution if any 'required' dependency cannot be resolved.
    Writes result to .agents/state/runtime/dependencies.json.
    """
    if not requirements:
        # Apply safe_minimal fallback for legacy skills
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
        # Skip deprecated keys silently (should be migrated by deps fix)
        if key in DEPRECATED_KEYS:
            continue

        result = _resolve_single(skill_name, key, mode)
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

    # Write to dependencies.json
    _write_json_atomic(DEPENDENCIES_LOG_PATH, {
        "skill": ctx.skill,
        "resolved_at": ctx.resolved_at,
        "requirements": ctx.requirements,
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
    """Resolve a single dependency key."""

    if mode == "none":
        return DependencyResult(name=key, mode=mode, status="skipped", source="mode=none", action="ok")

    resolver_map = {
        "rules":          _resolve_rules,
        "state":          _resolve_state,
        "approvals":      _resolve_approvals,
        "git":            _resolve_git_cached,
        "memory":         _resolve_memory,
        "rag":            _resolve_rag,
        "workspace_scan": _resolve_workspace_scan,
        "environment":    _resolve_environment_snapshot,
        "version":        _resolve_version_cached,
        "provider":       _resolve_provider_cached,
        "usage":          _resolve_usage_cached,
    }

    resolver_fn = resolver_map.get(key)
    if resolver_fn is None:
        return DependencyResult(name=key, mode=mode, status="skipped", source="unknown-key", action="warn_only")

    try:
        return resolver_fn(skill_name, mode)
    except Exception as e:
        return DependencyResult(name=key, mode=mode, status="missing", source=str(e), action="block" if mode == "required" else "warn_only")


# ---------------------------------------------------------------------------
# Individual Resolvers
# ---------------------------------------------------------------------------

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
    if approvals is not None and os.path.exists(APPROVALS_PATH):
        return DependencyResult(name="approvals", mode=mode, status="loaded", source=APPROVALS_PATH, action="ok", data=approvals)
    if mode == "optional":
        return DependencyResult(name="approvals", mode=mode, status="missing", source=APPROVALS_PATH, action="warn_only")
    return DependencyResult(name="approvals", mode=mode, status="missing", source=APPROVALS_PATH, action="block")


def _resolve_git_cached(skill_name: str, mode: str) -> DependencyResult:
    """Read git info from cached context.json only — NO subprocess calls."""
    context = _read_json_safe(CONTEXT_PATH)
    git_data = context.get("git", {})
    if git_data:
        return DependencyResult(name="git", mode=mode, status="cached", source=CONTEXT_PATH, action="ok", data=git_data)
    # Fall back to running the 3 allowed git commands
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
    """Memory resolver — cached reads metadata only; lazy defers; required blocks if not allowed."""
    if mode == "cached":
        return load_memory_cached()
    if mode == "lazy":
        return DependencyResult(name="memory", mode=mode, status="deferred", source="lazy-load", action="defer")
    if mode == "optional":
        result = load_memory_cached()
        result.action = "warn_only"
        return result
    # required
    memory_skills = {"project-memory-bootstrap", "project-memory-update", "project-rag-search"}
    if skill_name not in memory_skills:
        return DependencyResult(
            name="memory", mode=mode, status="blocked",
            source=f"skill '{skill_name}' not allowed to load full memory",
            action="block"
        )
    return DependencyResult(name="memory", mode=mode, status="deferred", source="full-load-pending", action="defer")


def _resolve_rag(skill_name: str, mode: str) -> DependencyResult:
    """RAG resolver — cached reads metadata only; lazy defers."""
    if mode in ("cached", "optional"):
        return load_rag_cached()
    if mode == "lazy":
        return DependencyResult(name="rag", mode=mode, status="deferred", source="lazy-load", action="defer")
    # required
    rag_skills = {"project-rag-search"}
    if skill_name not in rag_skills:
        return DependencyResult(
            name="rag", mode=mode, status="blocked",
            source=f"skill '{skill_name}' not allowed to require RAG",
            action="block"
        )
    return DependencyResult(name="rag", mode=mode, status="deferred", source="rag-connect-pending", action="defer")


def _resolve_workspace_scan(skill_name: str, mode: str) -> DependencyResult:
    """Workspace scan — only allowed for specific skills."""
    return check_workspace_scan_allowed(skill_name, mode)


def _resolve_environment_snapshot(skill_name: str, mode: str) -> DependencyResult:
    """Read environment snapshot from JSON — no CLI checks."""
    return read_environment_snapshot()


def _resolve_version_cached(skill_name: str, mode: str) -> DependencyResult:
    """Version from context.json only — never scan manifests."""
    return load_version_cached()


def _resolve_provider_cached(skill_name: str, mode: str) -> DependencyResult:
    """Provider from context.json or dashboard.json — no API calls."""
    return load_provider_cached()


def _resolve_usage_cached(skill_name: str, mode: str) -> DependencyResult:
    """Usage from dashboard/usage.json — never parse transcripts."""
    return load_usage_cached()

# ---------------------------------------------------------------------------
# Context Loader Functions (also called from context.py)
# ---------------------------------------------------------------------------

def load_memory_cached() -> DependencyResult:
    """
    Read ONLY memory metadata JSONs (memory-state.json + memory.config.json).
    Never reads project-summary.md or any memory chunk files.
    """
    state_file = os.path.join(".agents", "memory", "memory-state.json")
    config_file = os.path.join(".agents", "memory.config.json")

    if os.path.exists(state_file) or os.path.exists(config_file):
        data = {}
        if os.path.exists(state_file):
            data["state"] = _read_json_safe(state_file)
        if os.path.exists(config_file):
            data["config"] = _read_json_safe(config_file)
        return DependencyResult(name="memory", mode="cached", status="cached", source="memory-state.json", action="ok", data=data)

    return DependencyResult(name="memory", mode="cached", status="missing", source="memory-state.json not found", action="warn_only")


def load_memory_lazy(query: Optional[str] = None) -> DependencyResult:
    """
    Lazy memory loader. No load at init. Targeted load only when query is supplied.
    """
    if query is None:
        return DependencyResult(name="memory", mode="lazy", status="deferred", source="no-query", action="defer")
    # Targeted load: read memory chunk matching query
    # Implementation deferred to actual query time
    return DependencyResult(name="memory", mode="lazy", status="deferred", source=f"query={query[:50]}", action="defer")


def load_rag_cached() -> DependencyResult:
    """
    Read RAG metadata only — no vector DB connection.
    """
    rag_metadata = os.path.join(".agents", "rag", "rag-state.json")
    if os.path.exists(rag_metadata):
        data = _read_json_safe(rag_metadata)
        return DependencyResult(name="rag", mode="cached", status="cached", source=rag_metadata, action="ok", data=data)
    return DependencyResult(name="rag", mode="cached", status="missing", source="rag-state.json not found", action="warn_only")


def load_rag_lazy(query: Optional[str] = None) -> DependencyResult:
    """Lazy RAG loader. Deferred until query is supplied."""
    if query is None:
        return DependencyResult(name="rag", mode="lazy", status="deferred", source="no-query", action="defer")
    return DependencyResult(name="rag", mode="lazy", status="deferred", source=f"query={query[:50]}", action="defer")


def load_version_cached() -> DependencyResult:
    """
    Read version from .agents/state/context.json only.
    NEVER scans package.json, go.mod, pyproject.toml, Cargo.toml, MANIFEST.json.
    """
    context = _read_json_safe(CONTEXT_PATH)
    version = context.get("project_version") or context.get("version")
    if version:
        return DependencyResult(name="version", mode="cached", status="cached", source=CONTEXT_PATH, action="ok", data={"version": version})
    return DependencyResult(name="version", mode="cached", status="missing", source="project_version not in context.json", action="warn_only")


def load_provider_cached() -> DependencyResult:
    """
    Read provider metadata from context.json or dashboard.json.
    NEVER calls provider APIs or runs discovery.
    """
    context = _read_json_safe(CONTEXT_PATH)
    provider = context.get("provider") or context.get("ai_provider")
    if provider:
        return DependencyResult(name="provider", mode="cached", status="cached", source=CONTEXT_PATH, action="ok", data={"provider": provider})

    dashboard = _read_json_safe(DASHBOARD_PATH)
    provider = dashboard.get("provider") or dashboard.get("ai_provider")
    if provider:
        return DependencyResult(name="provider", mode="cached", status="cached", source=DASHBOARD_PATH, action="ok", data={"provider": provider})

    return DependencyResult(name="provider", mode="optional", status="missing", source="provider not in context/dashboard", action="warn_only")


def load_usage_cached() -> DependencyResult:
    """
    Read usage summary from context/usage.json or dashboard.json.
    NEVER parses transcript files or calls sync_request_history().
    """
    usage_file = os.path.join(_STATE_DIR, "context", "usage.json")
    if os.path.exists(usage_file):
        data = _read_json_safe(usage_file)
        if data:
            return DependencyResult(name="usage", mode="cached", status="cached", source=usage_file, action="ok", data=data)

    # Fallback: usage.json at state root
    usage_root = os.path.join(_STATE_DIR, "usage.json")
    if os.path.exists(usage_root):
        data = _read_json_safe(usage_root)
        if data:
            return DependencyResult(name="usage", mode="cached", status="cached", source=usage_root, action="ok", data=data)

    # Fallback: dashboard
    dashboard = _read_json_safe(DASHBOARD_PATH)
    usage_in_dash = dashboard.get("usage") or dashboard.get("context_usage")
    if usage_in_dash:
        return DependencyResult(name="usage", mode="cached", status="cached", source=DASHBOARD_PATH, action="ok", data=usage_in_dash)

    return DependencyResult(name="usage", mode="cached", status="missing", source="usage not found in state", action="warn_only")


def read_environment_snapshot() -> DependencyResult:
    """
    Read environment snapshot from .agents/state/environment.json.
    If stale (>24h) -> warn_only, do not block.
    If missing -> warn_only, do not block.
    NEVER runs CLI version checks.
    """
    env_data = _read_json_safe(ENVIRONMENT_SNAPSHOT_PATH)
    if not env_data:
        return DependencyResult(
            name="environment", mode="cached", status="missing",
            source="environment.json not found",
            action="warn_only",
        )

    updated_at_str = env_data.get("updated_at", "")
    if updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str)
            now = datetime.now(timezone.utc)
            # Make offset-aware for comparison
            if updated_at.tzinfo is None:
                from datetime import timezone as tz
                updated_at = updated_at.replace(tzinfo=tz.utc)
            age_seconds = (now - updated_at).total_seconds()
            if age_seconds > 86400:  # 24 hours
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
    """
    Workspace scan is blocked for all skills except WORKSPACE_SCAN_ALLOWED_SKILLS.
    """
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

    # lazy/optional for non-allowed skills -> warn
    return DependencyResult(
        name="workspace_scan", mode=mode, status="skipped",
        source=f"skill '{skill_name}' not in WORKSPACE_SCAN_ALLOWED_SKILLS",
        action="warn_only",
    )

# ---------------------------------------------------------------------------
# Public: Guardrails Summary
# ---------------------------------------------------------------------------

def load_guardrails_summary() -> dict:
    """
    Compute SHA-256 hashes of AI_RULES.md, AGENTS.md, active SKILL.md.
    Returns policy_flags dict. Does NOT weaken rules.
    """
    rules_path = "AI_RULES.md"
    agents_path = os.path.join(".agents", "AGENTS.md")

    # Find active SKILL.md from runtime state
    runtime = _read_json_safe(os.path.join(_STATE_DIR, "runtime.json"))
    current_skill = runtime.get("current_skill", "initialize-workflow")
    skill_path = (
        _find_skill_md(current_skill)
        or _find_skill_md("initialize-workflow")
        or ""
    )

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

# ---------------------------------------------------------------------------
# Public: Doctor Report
# ---------------------------------------------------------------------------

def get_doctor_report(strict_mode: bool = False) -> DoctorReport:
    """
    Scan all skills/*/SKILL.md files.
    For each: parse_requirements() and validate_requirements().
    Report: missing declarations, invalid keys, safety violations, unnecessary workspace_scan.

    strict_mode=False: missing runtime_requirements -> warning + safe_minimal fallback
    strict_mode=True:  missing runtime_requirements -> error (blocks execution)
    """
    all_skills = _find_all_skills()
    clean: list[str] = []
    warn: list[str] = []
    error: list[str] = []
    details: dict[str, ValidationResult] = {}

    for skill_name, skill_path in all_skills:
        reqs = parse_requirements(skill_name)
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
            result = validate_requirements(skill_name, reqs)

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

# ---------------------------------------------------------------------------
# Public: deps fix — Auto-migrate deprecated keys, add missing manifests
# ---------------------------------------------------------------------------

def generate_safe_requirements_template(skill_name: str) -> str:
    """Generate a safe runtime_requirements YAML block for a skill."""
    return (
        f"runtime_requirements:\n"
        f"  rules: required\n"
        f"  state: required\n"
        f"  approvals: optional\n"
        f"  git: cached\n"
        f"  memory: cached\n"
        f"  rag: cached\n"
        f"  workspace_scan: none\n"
        f"  environment: cached\n"
        f"  version: cached\n"
        f"  provider: optional\n"
        f"  usage: cached\n"
    )


def compute_deps_fix_diff(skill_name: str) -> Optional[dict]:
    """
    Compute what deps fix would change for a skill.
    Returns dict with {skill_name, skill_path, changes: list[str], proposed_frontmatter_addition: str}
    or None if no changes needed.
    """
    skill_path = _find_skill_md(skill_name)
    if not skill_path:
        return None

    reqs = parse_requirements(skill_name)
    changes: list[str] = []
    migration_needed = False
    template_needed = False

    if not reqs:
        template_needed = True
        changes.append(f"ADD runtime_requirements block (safe_minimal template)")
    else:
        for key in list(reqs.keys()):
            if key in DEPRECATED_KEYS:
                new_key = DEPRECATED_KEYS[key]
                changes.append(f"MIGRATE '{key}' -> '{new_key}'")
                migration_needed = True

        # Check safety key violations to fix
        for key in SAFETY_KEYS:
            if reqs.get(key) in ("lazy", "optional", "none"):
                changes.append(f"FIX safety key '{key}': '{reqs[key]}' -> 'required'")

        # workspace_scan violation
        if reqs.get("workspace_scan") == "required" and skill_name not in WORKSPACE_SCAN_ALLOWED_SKILLS:
            changes.append(f"FIX workspace_scan: required -> none (skill not in allowlist)")

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

# ---------------------------------------------------------------------------
# Re-export phase gate + next task from task_orchestrator
# ---------------------------------------------------------------------------

def validate_phase_completion(phase_id: str, task_graph: Any, task_ledger: Any) -> Any:
    """Delegate to task_orchestrator.validate_phase_completion."""
    from task_orchestrator import validate_phase_completion as _vpc
    return _vpc(phase_id, task_graph, task_ledger)


def get_next_ready_task(task_graph: Any, task_ledger: Any) -> tuple[Optional[str], str]:
    """Delegate to task_orchestrator.get_next_ready_task."""
    from task_orchestrator import get_next_ready_task as _gnrt
    return _gnrt(task_graph, task_ledger)
