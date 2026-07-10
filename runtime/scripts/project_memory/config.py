import os
import json
import common
from common import log_warn


DEFAULT_CONFIG = {
    "project_id": "ai-skill-framework",
    "memory_root": ".agents/memory",
    "vector_provider": "qdrant",
    "vector_collection": "ai-skill-framework",
    "qmd_index": ".agents/memory/qmd.index"
}

def load_memory_config(config_path: str = None) -> dict:
    root = common.get_project_root()

    if not config_path:
        config_path = os.path.join(root, ".agents", "memory.config.json")
    
    if not os.path.exists(config_path):
        # Fallback to root directory check
        alt_path = os.path.join(root, "memory.config.json")
        if os.path.exists(alt_path):
            config_path = alt_path
        else:
            return DEFAULT_CONFIG
            
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Merge with default to ensure all keys present
            for k, v in DEFAULT_CONFIG.items():
                if k not in config:
                    config[k] = v
            return config
    except Exception as e:
        log_warn(f"Failed to load memory configuration: {e}. Using defaults.")
        return DEFAULT_CONFIG

def get_memory_paths(config: dict) -> dict:
    root = common.get_project_root()
    mem_root = config.get("memory_root", ".agents/memory")

    # Resolve relative path to absolute or project root relative
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
