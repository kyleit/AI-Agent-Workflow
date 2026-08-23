# environment_health.py
from __future__ import annotations

import subprocess
import sys
from typing import Any


def get_tool_version(cmd: list[str]) -> str:
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return res.stdout.strip().splitlines()[0]
    except Exception:
        return "not installed"


def run_health_check() -> dict[str, Any]:
    os_name = sys.platform
    git_ver = get_tool_version(["git", "--version"])
    python_ver = sys.version.strip().splitlines()[0]
    node_ver = get_tool_version(["node", "--version"])
    docker_ver = get_tool_version(["docker", "--version"])
    sqlite_ver = get_tool_version(["sqlite3", "--version"])
    tree_sitter = get_tool_version(["tree-sitter", "--version"])

    health = {
        "os": os_name,
        "tools": {
            "git": git_ver,
            "python": python_ver,
            "node": node_ver,
            "docker": docker_ver,
            "sqlite": sqlite_ver,
            "tree-sitter": tree_sitter
        },
        "status": "healthy"
    }

    warnings: list[str] = []
    if git_ver == "not installed":
        warnings.append("Git is not installed on PATH.")
        health["status"] = "degraded"
    if sqlite_ver == "not installed":
        warnings.append("SQLite is not installed on PATH.")
        health["status"] = "degraded"

    return {
        "status": "success",
        "command": "env health",
        "summary": f"Environment health: {health['status']}. Platform: {os_name}.",
        "warnings": warnings,
        "files_read": [],
        "files_written": [],
        "health": health
    }


__all__ = [
    "get_tool_version",
    "run_health_check",
]
