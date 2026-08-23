"""Hard-gated MCP config writers for Claude / Codex / Antigravity.

Per AI_RULES §15 these are HARD-GATED: every writer is dry-run by default,
produces a ``.bak`` before editing, and ``apply`` refuses unless ``approved`` is
explicitly True (granted only after the owner OKs the specific write). Merges are
non-destructive: JSON merges only the ``mcpServers.devteam`` key; TOML appends a
``[mcp_servers.devteam]`` block only if absent.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass

from ..fs.atomic import atomic_write
from .engine_installer import global_home


@dataclass(frozen=True)
class ConfigChange:
    tool: str
    path: str
    action: str  # "merge-json" | "append-toml-block"
    diff: str
    backup_path: str


def _server_path() -> str:
    return os.path.join(global_home(), "mcp", "server.py").replace("\\", "/")


def _server_spec() -> dict:
    return {"command": "python", "args": [_server_path()]}


def _toml_block() -> str:
    return (
        "[mcp_servers.devteam]\n"
        'command = "python"\n'
        f'args = ["{_server_path()}"]\n'
    )


def plan_claude(root: str) -> ConfigChange:
    path = os.path.join(root, ".mcp.json")
    return ConfigChange("claude", path, "merge-json",
                        f'mcpServers.devteam = {json.dumps(_server_spec())}', path + ".bak")


def plan_codex() -> ConfigChange:
    path = os.path.join(os.path.expanduser("~"), ".codex", "config.toml")
    return ConfigChange("codex", path, "append-toml-block", _toml_block(), path + ".bak")


def plan_antigravity() -> ConfigChange:
    path = os.path.join(os.path.expanduser("~"), ".antigravity", "mcp_config.json")
    return ConfigChange("antigravity", path, "merge-json",
                        f'mcpServers.devteam = {json.dumps(_server_spec())}', path + ".bak")


def plan_all(root: str) -> list[ConfigChange]:
    return [plan_claude(root), plan_codex(), plan_antigravity()]


def _merge_json(path: str) -> None:
    data: dict = {}
    if os.path.exists(path):
        raw = open(path, encoding="utf-8-sig").read().strip()
        if raw:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                data = loaded
    servers = data.get("mcpServers")
    if not isinstance(servers, dict):
        servers = {}
    servers["devteam"] = _server_spec()
    data["mcpServers"] = servers
    atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def _append_toml(path: str) -> bool:
    text = open(path, encoding="utf-8-sig").read() if os.path.exists(path) else ""
    if "[mcp_servers.devteam]" in text:
        return False
    sep = "" if (text == "" or text.endswith("\n")) else "\n"
    atomic_write(path, text + sep + "\n" + _toml_block())
    return True


def apply(change: ConfigChange, approved: bool) -> dict:
    """Apply a config change. Refuses unless the owner approved this write."""
    if not approved:
        return {
            "applied": False,
            "tool": change.tool,
            "reason": "HARD-GATED: owner approval required (§15); pass approved=True after OK",
            "would_write": change.path,
        }
    os.makedirs(os.path.dirname(change.path), exist_ok=True)
    backed_up = False
    if os.path.exists(change.path):
        shutil.copyfile(change.path, change.backup_path)
        backed_up = True
    if change.action == "merge-json":
        _merge_json(change.path)
        changed = True
    elif change.action == "append-toml-block":
        changed = _append_toml(change.path)
    else:  # pragma: no cover - guarded by construction
        return {"applied": False, "tool": change.tool, "reason": f"unknown action {change.action}"}
    return {
        "applied": changed,
        "tool": change.tool,
        "path": change.path,
        "backup": change.backup_path if backed_up else None,
        "note": "already present" if not changed else "merged",
    }
