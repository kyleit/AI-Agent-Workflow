from __future__ import annotations

import os
from typing import Any

from .common import get_project_root, log_warn, read_json_safe

DEFAULT_CONFIG = {
    "project_id": "ai-skill-framework",
    "memory_root": ".agents/memory",
    "vector_provider": "qdrant",
    "vector_collection": "ai-skill-framework",
    "qmd_index": ".agents/memory/qmd.index"
}


def load_memory_config(config_path: str | None = None, root_dir: str | None = None) -> dict[str, Any]:
    root = root_dir or get_project_root()

    if not config_path:
        config_path = os.path.join(root, ".agents", "memory.config.json")

    if not os.path.exists(config_path):
        alt_path = os.path.join(root, "memory.config.json")
        if os.path.exists(alt_path):
            config_path = alt_path
        else:
            merged = dict(DEFAULT_CONFIG)
            merged["project_id"] = os.path.basename(os.path.abspath(root)) or "ai-skill-framework"
            return merged

    config = read_json_safe(config_path)
    if isinstance(config, dict):
        for k, v in DEFAULT_CONFIG.items():
            if k not in config:
                config[k] = v
        return config

    log_warn("Failed to load memory configuration. Using defaults.")
    merged = dict(DEFAULT_CONFIG)
    merged["project_id"] = os.path.basename(os.path.abspath(root)) or "ai-skill-framework"
    return merged


def get_memory_paths(config: dict[str, Any], root_dir: str | None = None) -> dict[str, Any]:
    root = root_dir or get_project_root()
    mem_root = config.get("memory_root", ".agents/memory")
    full_mem_root = os.path.join(root, mem_root)

    return {
        "memory_root": full_mem_root,
        "summary": os.path.join(full_mem_root, "project-summary.md"),
        "state": os.path.join(full_mem_root, "memory-state.json"),
        "lessons_dir": os.path.join(full_mem_root, "lessons"),
        "architecture_dir": os.path.join(full_mem_root, "architecture"),
        "rag_dir": os.path.join(full_mem_root, "rag"),
        "vector_sync_plan": os.path.join(full_mem_root, "rag", "vector-sync-plan.json"),
        "known_problems": os.path.join(full_mem_root, "lessons", "known-problems.md"),
        "architectural_decisions": os.path.join(full_mem_root, "lessons", "architectural-decisions.md")
    }


__all__ = ["DEFAULT_CONFIG", "load_memory_config", "get_memory_paths"]
