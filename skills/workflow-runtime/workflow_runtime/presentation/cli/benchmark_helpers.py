from __future__ import annotations

import json
import os
import sys
from typing import Any

# benchmark_helpers.py
"""Shared benchmark helpers for init flow tests."""

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

MANDATORY_FIELDS = [
    "git_branch", "git_working_tree", "is_git_repository",
    "checkpoint", "work_item_id",
    "rules_loaded", "approvals_loaded", "state_loaded",
    "version",
]


def _write_json(path: str, data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _file_size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except Exception:
        return 0


def setup_workspace(tmp_dir: str, ctx: dict[str, Any]) -> None:
    """Create a realistic fake workspace with state files."""
    state_dir = os.path.join(tmp_dir, ".agents", "state")
    memory_dir = os.path.join(tmp_dir, ".agents", "memory")
    os.makedirs(state_dir, exist_ok=True)
    os.makedirs(memory_dir, exist_ok=True)

    # context.json
    work_item = {"type": "FEAT", "id": "FEAT-050", "title": "Lightweight Runtime Init"} if ctx.get("has_work_item") else {"type": "None", "id": "None", "title": "None"}
    _write_json(os.path.join(state_dir, "context.json"), {
        "workspace_path": ".",
        "checkpoint": ctx.get("checkpoint", 1),
        "project_version": "2.5.0",
        "version_source": "context.json",
        "work_item": work_item,
        "git": {
            "branch": ctx.get("new_branch", "main"),
            "working_tree": "clean" if ctx.get("git_clean") else "dirty",
            "is_git_repository": True,
        },
        "updated_at": "2026-07-11T00:00:00+07:00",
    })

    # approvals.json
    _write_json(os.path.join(state_dir, "approvals.json"), {
        "blueprint": {"FEAT-050": {"approved": True, "approved_at": "2026-07-10T10:00:00Z"}},
        "updated_at": "2026-07-10T10:00:00Z",
    })

    # runtime.json
    _write_json(os.path.join(state_dir, "runtime.json"), {
        "status": "completed",
        "current_skill": "initialize-workflow",
        "checkpoint": ctx.get("checkpoint", 1),
        "updated_at": "2026-07-10T09:00:00Z",
    })

    # environment.json (stale nếu UC-4)
    env_ts = "2026-07-09T00:00:00Z" if ctx.get("env_stale") else "2026-07-11T00:00:00Z"
    _write_json(os.path.join(state_dir, "environment.json"), {
        "os": "Windows",
        "python": "3.14.4",
        "node": "22.0.0",
        "git": "2.45.0",
        "updated_at": env_ts,
    })

    # memory-state.json (metadata only)
    if ctx.get("has_memory"):
        _write_json(os.path.join(memory_dir, "memory-state.json"), {
            "status": "ready",
            "chunk_count": 48,
            "last_updated": "2026-07-10T12:00:00Z",
            "total_size_kb": 1240,
        })
        # Simulate heavy memory file (project-summary.md ~1.2MB)
        summary_path = os.path.join(memory_dir, "project-summary.md")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("# Project Summary\n" + ("This is a large summary file. " * 2000) + "\n")

    # AI_RULES.md stub
    with open(os.path.join(tmp_dir, "AI_RULES.md"), "w", encoding="utf-8") as f:
        f.write("# AI Rules\n## Approval Gate Policy\n" + ("Rule content. " * 100) + "\n")

    # .agents/AGENTS.md stub
    os.makedirs(os.path.join(tmp_dir, ".agents"), exist_ok=True)
    with open(os.path.join(tmp_dir, ".agents", "AGENTS.md"), "w", encoding="utf-8") as f:
        f.write("# AIWF Agents\n" + ("Agent rules. " * 50) + "\n")

    # Fake package.json (for old init manifest scan test)
    with open(os.path.join(tmp_dir, "package.json"), "w", encoding="utf-8") as f:
        json.dump({"name": "aiwf", "version": "2.5.0"}, f)

    # Fake go.mod
    with open(os.path.join(tmp_dir, "go.mod"), "w", encoding="utf-8") as f:
        f.write("module github.com/aiwf\ngo 1.22\n")


def compute_accuracy(result: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    present: list[str] = [f for f in MANDATORY_FIELDS if result.get(f) not in (None, "", "None", False)]
    missing: list[str] = [f for f in MANDATORY_FIELDS if f not in present]
    score = len(present) / len(MANDATORY_FIELDS)
    return round(score, 2), present, missing


__all__ = [
    "MANDATORY_FIELDS",
    "_file_size",
    "setup_workspace",
    "compute_accuracy",
]
