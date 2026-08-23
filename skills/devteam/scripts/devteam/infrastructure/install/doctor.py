"""DevTeam doctor — read-only health check of the global install + repo wiring."""

from __future__ import annotations

import importlib.util
import json
import os

from ..paths import PathResolver
from .engine_installer import global_home


def _chk(name: str, ok: bool, detail: str) -> dict:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _home(*parts: str) -> str:
    return os.path.join(os.path.expanduser("~"), *parts)


def _json_has_devteam(path: str) -> bool:
    if not os.path.exists(path):
        return False
    try:
        data = json.loads(open(path, encoding="utf-8-sig").read() or "{}")
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and "devteam" in (data.get("mcpServers") or {})


def run_doctor(root: str | None = None) -> dict:
    resolved = root or PathResolver.discover_root()
    home = global_home()
    checks: list[dict] = []

    engine = os.path.join(home, "engine", "devteam", "__init__.py")
    checks.append(_chk("engine_installed", os.path.exists(engine), os.path.dirname(engine)))

    server = os.path.join(home, "mcp", "server.py")
    checks.append(_chk("mcp_server_present", os.path.exists(server), server))

    mcp_ok = importlib.util.find_spec("mcp") is not None
    checks.append(_chk("mcp_package", mcp_ok, "importable" if mcp_ok else "run: pip install mcp"))

    adapters = {
        "adapter_claude": _home(".claude", "commands", "seat.md"),
        "adapter_codex": _home(".codex", "skills", "seat", "SKILL.md"),
        "adapter_antigravity": _home(".antigravity", "workflows", "seat.workflow.md"),
    }
    for name, p in adapters.items():
        checks.append(_chk(name, os.path.exists(p), p))

    claude_cfg = os.path.join(resolved, ".mcp.json")
    checks.append(_chk("config_claude", _json_has_devteam(claude_cfg), claude_cfg))

    codex_cfg = _home(".codex", "config.toml")
    codex_ok = os.path.exists(codex_cfg) and "[mcp_servers.devteam]" in open(
        codex_cfg, encoding="utf-8-sig"
    ).read()
    checks.append(_chk("config_codex", codex_ok, codex_cfg))

    anti_cfg = _home(".antigravity", "mcp_config.json")
    checks.append(_chk("config_antigravity", _json_has_devteam(anti_cfg), anti_cfg))

    seats = os.path.join(resolved, ".agents", "devteam", "seats.json")
    checks.append(_chk("repo_initialized", os.path.exists(seats), seats + " (run: devteam init --apply)"))

    required = {c["name"] for c in checks} - {"repo_initialized"}  # repo init is per-repo, advisory
    ok_all = all(c["ok"] for c in checks if c["name"] in required)
    failed = [c["name"] for c in checks if not c["ok"]]
    return {"ok": ok_all, "checks": checks, "failed": failed, "home": home, "repo": resolved}
