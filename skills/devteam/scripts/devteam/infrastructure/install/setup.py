"""DevTeam one-shot setup — engine + adapters + (optional) mcp + (gated) configs.

Single command:  python -m devteam setup --write-configs --mcp

Config writes are HARD-GATED (§15): they run ONLY when ``write_configs`` is True
(the ``--write-configs`` flag is the owner's explicit approval, dry-run otherwise).
Installing the ``mcp`` package runs ONLY when ``with_mcp`` is True.
"""

from __future__ import annotations

import subprocess
import sys

from ..paths import PathResolver
from . import config_writers as cw
from .adapters_installer import install_adapters
from .doctor import run_doctor
from .engine_installer import install_engine


def _pip_install_mcp() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "mcp"],
        capture_output=True,
        text=True,
    )
    tail = (proc.stdout or "").strip().splitlines()[-1:] or [""]
    return {"ok": proc.returncode == 0, "tail": tail[0], "returncode": proc.returncode}


def run_setup(root: str | None = None, write_configs: bool = False, with_mcp: bool = False) -> dict:
    resolved = root or PathResolver.discover_root()
    result: dict = {
        "engine": install_engine(force=True),
        "adapters": install_adapters(),
    }
    if with_mcp:
        result["mcp_pip"] = _pip_install_mcp()

    configs = [cw.apply(ch, approved=write_configs) for ch in cw.plan_all(resolved)]
    result["configs"] = configs
    result["configs_written"] = write_configs
    if not write_configs:
        result["hint"] = "re-run with --write-configs to register MCP in Claude/Codex/Antigravity"
    result["doctor"] = run_doctor(resolved)
    return result
