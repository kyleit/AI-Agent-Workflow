"""Resolve shared assets without materializing them in each project."""
from __future__ import annotations

import json
import os
from pathlib import Path


def skill_roots(workspace: Path | str = ".") -> list[Path]:
    project = Path(workspace).resolve()
    candidates: list[Path] = []
    for key in ("AIWF_GLOBAL_SOURCE", "AIWF_HOME", "AIWF_GLOBAL_ROOT", "AIWF_FRAMEWORK_ROOT"):
        if value := os.environ.get(key):
            root = Path(value).expanduser()
            candidates.extend((root / "skills", root / ".agents" / "skills"))
    home = Path.home()
    try:
        marker = json.loads((home / ".agents" / "aiwf-global.json").read_text(encoding="utf-8-sig"))
        if isinstance(marker, dict) and marker.get("home_root"):
            candidates.append(Path(str(marker["home_root"])) / "skills")
    except (OSError, ValueError):
        pass
    # The executing package is itself a shared installation, including when
    # loaded from a Codex junction or an unpacked release without .git.
    candidates.extend((Path(__file__).resolve().parents[4], home / ".agents" / "skills",
                       home / ".codex" / "skills", project / "skills", project / ".agents" / "skills"))
    roots: list[Path] = []
    for path in candidates:
        path = path.resolve()
        if path.is_dir() and path not in roots:
            roots.append(path)
    return roots


def shared_framework_root(workspace: Path | str = ".") -> Path | None:
    project = Path(workspace).resolve()
    for root in skill_roots(project):
        if (root / "workflow-runtime").is_dir() and root not in (project / "skills", project / ".agents" / "skills"):
            return root.parent
    return None


def registry_path(workspace: Path | str = ".") -> Path:
    project = Path(workspace).resolve()
    local = project / ".agents" / "config" / "skill-registry.json"
    if local.is_file():
        return local
    return next((root / "registry.json" for root in skill_roots(project)
                 if (root / "registry.json").is_file()), local)
