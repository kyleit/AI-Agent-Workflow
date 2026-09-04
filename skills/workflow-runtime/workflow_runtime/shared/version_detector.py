from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, cast

_STATE_DIR = os.path.join(".agents", "state")
_CONTEXT_PATH = os.path.join(_STATE_DIR, "context.json")

def _read_json_safe(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data: Any = json.load(f)
            if isinstance(data, dict):
                return cast(dict[str, Any], data)
            return {}
    except Exception:
        return {}


def detect_project_version_cached() -> dict[str, Any]:
    """
    Read project version from .agents/state/context.json only.
    NEVER scans package.json, go.mod, pyproject.toml, Cargo.toml, or MANIFEST.json.
    NEVER runs git describe --tags.
    """
    context = _read_json_safe(_CONTEXT_PATH)
    version = context.get("project_version") or context.get("version")
    if version:
        return {"version": str(version), "source": "context.json"}

    # Fallback: read only .agents/MANIFEST.json (framework version)
    manifest_path = os.path.join(".agents", "MANIFEST.json")
    if os.path.exists(manifest_path):
        manifest = _read_json_safe(manifest_path)
        m_ver = manifest.get("version")
        if m_ver:
            return {"version": str(m_ver), "source": "MANIFEST.json"}

    return {"version": "0.0.0", "source": "unknown"}


def detect_framework_version() -> dict[str, Any]:
    """Read the framework manifest without inheriting a project's version."""
    configured = (
        os.environ.get("AIWF_FRAMEWORK_ROOT"),
        os.environ.get("AIWF_GLOBAL_ROOT"),
        os.environ.get("AIWF_GLOBAL_SOURCE"),
    )
    candidates: list[Path] = [Path(value) for value in configured if value]
    candidates.extend(Path(__file__).resolve().parents)
    seen: set[Path] = set()
    for root in candidates:
        for manifest_path in (root / "MANIFEST.json", root / ".agents" / "MANIFEST.json"):
            resolved = manifest_path.resolve()
            if resolved in seen or not resolved.is_file():
                continue
            seen.add(resolved)
            manifest = _read_json_safe(str(resolved))
            version = manifest.get("version")
            if version:
                return {"version": str(version), "source": str(resolved)}
    return {"version": "0.0.0", "source": "unknown"}
