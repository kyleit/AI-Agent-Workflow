# dependency_resolver.py
from __future__ import annotations 
import os
import sys
from dataclasses import dataclass, field
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
    errors: list[str] = field(default_factory=list[str])
    warnings: list[str] = field(default_factory=list[str])


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
    requirements: dict[str, Any]
    resolved: dict[str, DependencyResult]
    missing_required: list[str] = field(default_factory=list[str])
    warnings: list[str] = field(default_factory=list[str])


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
