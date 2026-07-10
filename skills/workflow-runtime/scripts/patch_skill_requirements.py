#!/usr/bin/env python3
"""
patch_skill_requirements.py
FEAT-050 Task 4.1: Add tailored runtime_requirements to all SKILL.md files.

Each skill gets a customized requirements block matching its actual behavior.
"""
import os
import sys

# ---------------------------------------------------------------------------
# Tailored requirements per skill
# Format: {skill_name: {key: mode, ...}}
# ---------------------------------------------------------------------------

SKILL_REQUIREMENTS = {
    # ─── Orchestration & Routing ─────────────────────────────────────────────
    "orchestrator": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "cached",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "software-development-workflow": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "cached",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "resume-workflow": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "cached",
        "rag": "none",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "workflow-runtime": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "none",
        "rag": "none",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "knowledge-runtime": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "lazy",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "none",
        "provider": "optional",
        "usage": "none",
    },

    # ─── Discovery & Brainstorming ────────────────────────────────────────────
    "brainstorming": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "none",
        "provider": "optional",
        "usage": "cached",
    },
    "project-discovery": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "none",
        "rag": "none",
        "workspace_scan": "required",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "none",
    },

    # ─── Planning ─────────────────────────────────────────────────────────────
    "brainstorming-to-plan": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "plan-to-blueprint": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "blueprint-to-implementation": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "create-adr": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "cached",
        "provider": "optional",
        "usage": "none",
    },

    # ─── Quick Workflows ──────────────────────────────────────────────────────
    "quick-feature": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "quick-fix": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },

    # ─── Implementation & Review ──────────────────────────────────────────────
    "implementation-to-debug": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "debug-to-verify": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },
    "implementation-to-release": {
        "rules": "required",
        "state": "required",
        "approvals": "required",
        "git": "cached",
        "memory": "cached",
        "rag": "none",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "cached",
    },

    # ─── Memory & RAG ─────────────────────────────────────────────────────────
    "project-memory-bootstrap": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "required",
        "rag": "optional",
        "workspace_scan": "required",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "none",
    },
    "project-memory-update": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "required",
        "rag": "optional",
        "workspace_scan": "required",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "none",
    },
    "project-rag-search": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "none",
        "memory": "cached",
        "rag": "required",
        "workspace_scan": "none",
        "environment": "none",
        "version": "none",
        "provider": "optional",
        "usage": "none",
    },

    # ─── Environment & Health ─────────────────────────────────────────────────
    "environment-bootstrap": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "none",
        "rag": "none",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "none",
    },
    "environment-health": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "none",
        "rag": "none",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "cached",
        "provider": "optional",
        "usage": "none",
    },

    # ─── Frontend ─────────────────────────────────────────────────────────────
    "frontend-design": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "none",
        "provider": "optional",
        "usage": "none",
    },
    "frontend-visual-debug": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "cached",
        "rag": "lazy",
        "workspace_scan": "none",
        "environment": "none",
        "version": "none",
        "provider": "optional",
        "usage": "none",
    },

    # ─── Verification & Quality ───────────────────────────────────────────────
    "skill-self-verification": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "cached",
        "memory": "none",
        "rag": "none",
        "workspace_scan": "none",
        "environment": "cached",
        "version": "none",
        "provider": "optional",
        "usage": "none",
    },
    "okr-report-generator": {
        "rules": "required",
        "state": "required",
        "approvals": "optional",
        "git": "none",
        "memory": "none",
        "rag": "none",
        "workspace_scan": "none",
        "environment": "none",
        "version": "none",
        "provider": "optional",
        "usage": "none",
    },
}

# Safe minimal fallback for any skill not listed above
SAFE_MINIMAL = {
    "rules": "required",
    "state": "required",
    "approvals": "optional",
    "git": "cached",
    "memory": "cached",
    "rag": "cached",
    "workspace_scan": "none",
    "environment": "cached",
    "version": "cached",
    "provider": "optional",
    "usage": "cached",
}


def build_requirements_block(requirements: dict) -> str:
    lines = ["runtime_requirements:"]
    for key, mode in requirements.items():
        lines.append(f"  {key}: {mode}")
    return "\n".join(lines) + "\n"


def patch_skill_md(skill_md_path: str, skill_name: str, requirements: dict) -> bool:
    """Inject runtime_requirements into a SKILL.md frontmatter. Returns True if changed."""
    try:
        with open(skill_md_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"  [ERROR] Cannot read {skill_md_path}: {e}")
        return False

    # Check if already has runtime_requirements
    if "runtime_requirements:" in content:
        print(f"  [SKIP] {skill_name}: already has runtime_requirements")
        return False

    # Must have frontmatter
    if not content.startswith("---"):
        print(f"  [WARN] {skill_name}: no YAML frontmatter, skipping")
        return False

    parts = content.split("---", 2)
    if len(parts) < 3:
        print(f"  [WARN] {skill_name}: malformed frontmatter, skipping")
        return False

    req_block = build_requirements_block(requirements)
    # Insert before closing ---
    new_fm = parts[1].rstrip() + "\n" + req_block
    new_content = "---" + new_fm + "---" + parts[2]

    try:
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    except Exception as e:
        print(f"  [ERROR] Cannot write {skill_md_path}: {e}")
        return False


def main():
    skill_bases = ["skills", os.path.join(".agents", "skills")]
    total_patched = 0
    total_skipped = 0
    total_error = 0

    for base_dir in skill_bases:
        if not os.path.isdir(base_dir):
            continue
        for skill_name in sorted(os.listdir(base_dir)):
            skill_md = os.path.join(base_dir, skill_name, "SKILL.md")
            if not os.path.exists(skill_md):
                continue

            requirements = SKILL_REQUIREMENTS.get(skill_name, SAFE_MINIMAL)
            print(f"Patching: {skill_name}")
            changed = patch_skill_md(skill_md, skill_name, requirements)
            if changed:
                print(f"  [OK]   {skill_md}")
                total_patched += 1
            else:
                total_skipped += 1

    print(f"\nDone: {total_patched} patched, {total_skipped} skipped, {total_error} errors")


if __name__ == "__main__":
    main()
