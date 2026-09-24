"""Resolve where the framework is installed when a project links to it.

A project installed in linked mode holds no copy of the framework's skills; its
runtime link descriptor names the global install instead. Both the gate-runner
search and the authoring-audit baseline need that location, so it is read in
exactly one place.
"""

from __future__ import annotations

import json
from pathlib import Path

LINKED_BRIDGE_MODES = frozenset({"global_link", "global_adapter"})


def linked_install_root(workspace_root: Path) -> Path | None:
    """Return the global install root for a linked project, or None.

    None means the project is not linked, the descriptor is absent or malformed,
    or the named root does not exist. None of those is an error; the caller simply
    has no linked install to consult.
    """
    descriptor = workspace_root / ".agents" / "runtime-link.json"
    try:
        payload = json.loads(descriptor.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("bridge_mode") or "") not in LINKED_BRIDGE_MODES:
        return None
    global_root = payload.get("global_root")
    if not global_root:
        return None
    candidate = Path(str(global_root)).expanduser()
    return candidate if candidate.is_dir() else None


__all__ = ["LINKED_BRIDGE_MODES", "linked_install_root"]
