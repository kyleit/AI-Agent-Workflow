from __future__ import annotations

import os
from pathlib import Path


def _is_project_root(path: Path) -> bool:
    return (path / ".agents" / "AI_RULES.md").is_file() or (path / "AI_RULES.md").is_file()


def _is_global_source(path: Path) -> bool:
    return (path / ".git").exists() and (
        (path / "MANIFEST.json").is_file()
        or (path / "skills" / "workflow-runtime").is_dir()
        or (path / ".agents" / "skills" / "workflow-runtime").is_dir()
    )


def resolve_global_source(project_root: Path | str | None = None) -> Path | None:
    """Resolve a dedicated global source checkout without project fallback.

    The current project is deliberately rejected when it is also the only
    candidate. This keeps ``update --all`` from treating a dirty project as
    the global installation and makes the degraded result explicit.
    """
    project = Path(project_root or Path.cwd()).expanduser().resolve()
    configured = [
        os.environ.get("AIWF_GLOBAL_SOURCE"),
        os.environ.get("AIWF_HOME"),
        os.environ.get("AIWF_GLOBAL_ROOT"),
        os.environ.get("AIWF_FRAMEWORK_ROOT"),
    ]
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    configured.extend([
        str(home / ".aiwf" / "source"),
        str(home / ".aiwf" / "source" / "AI-Agent-Workflow"),
        os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local")) + "/aiwf/source",
    ])
    seen: set[Path] = set()
    for raw in configured:
        if not raw:
            continue
        candidate = Path(raw).expanduser().resolve()
        if candidate in seen or candidate == project:
            continue
        seen.add(candidate)
        if candidate.name == "source" and not _is_global_source(candidate):
            nested = candidate / "AI-Agent-Workflow"
            if _is_global_source(nested):
                candidate = nested
        if _is_global_source(candidate) and not _is_project_root(candidate):
            return candidate
        if _is_global_source(candidate) and candidate != project:
            return candidate
    return None


__all__ = ["resolve_global_source"]
