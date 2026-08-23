from __future__ import annotations

from typing import Optional

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

import os
import sys

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


__all__ = [
    "_find_skill_md",
    "_find_all_skills",
]
