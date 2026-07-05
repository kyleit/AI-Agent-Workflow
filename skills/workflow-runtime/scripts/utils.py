# utils.py
import os
import json

def get_memory_info() -> dict:
    info = {"status": "UNKNOWN", "last_updated": "N/A"}
    if os.path.exists(".agents/memory.config.json"):
        try:
            with open(".agents/memory.config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                info["status"] = "FRESH"
                info["last_updated"] = data.get("last_updated", "N/A")
        except (json.JSONDecodeError, IOError):
            pass
    return info

def get_rag_info() -> dict:
    info = {"connected": False, "provider": "unknown"}
    # Standard check of memory.config.json for RAG provider
    if os.path.exists(".agents/memory.config.json"):
        try:
            with open(".agents/memory.config.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                info["connected"] = True
                info["provider"] = data.get("rag", {}).get("provider", "qdrant")
        except (json.JSONDecodeError, IOError):
            pass
    else:
        # Default fallback
        info["connected"] = True
        info["provider"] = "qdrant"
    return info
