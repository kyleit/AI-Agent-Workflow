"""Install the per-tool seat adapters to their user-global locations.

Idempotent file copies. Reversible (delete the files). No config edits here —
MCP registration is handled by ``config_writers`` (hard-gated).
"""

from __future__ import annotations

import os
import shutil


def _skill_root() -> str:
    # this file: .../devteam/infrastructure/install/adapters_installer.py
    # skill root = .../skills/devteam
    here = os.path.abspath(__file__)
    pkg = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(here))))
    return os.path.dirname(pkg) if os.path.basename(pkg) == "scripts" else pkg


def _home(*parts: str) -> str:
    return os.path.join(os.path.expanduser("~"), *parts)


def install_adapters() -> dict:
    root = _skill_root()
    adapters = os.path.join(root, "adapters")
    installed: list[str] = []
    skipped: list[str] = []

    targets = [
        (os.path.join(adapters, "claude", "seat.md"), _home(".claude", "commands", "seat.md")),
        (os.path.join(adapters, "codex", "SKILL.md"), _home(".codex", "skills", "seat", "SKILL.md")),
        (os.path.join(adapters, "antigravity", "seat.workflow.md"),
         _home(".antigravity", "workflows", "seat.workflow.md")),
    ]
    for src, dest in targets:
        if not os.path.exists(src):
            skipped.append(f"missing source: {src}")
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)
        installed.append(dest)
    return {"installed": installed, "skipped": skipped}
