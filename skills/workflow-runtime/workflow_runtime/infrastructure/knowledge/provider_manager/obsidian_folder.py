"""Resolve (and provision) the per-project folder inside a shared Obsidian vault."""

from __future__ import annotations

import datetime
import json
import os
import re
import warnings
from typing import Any, cast

from workflow_runtime.infrastructure.knowledge.provider_manager.config import (
    load_project_config, resolve_provider_config)
from workflow_runtime.infrastructure.knowledge.provider_manager.masking import \
    mask_secrets

DEFAULT_FOLDER_PATTERN: str = "AIWF-Knowledge-{project_slug}"
PROJECT_MAP_RELPATH: tuple[str, str, str] = (".agents", "knowledge", "obsidian-project-map.json")

# Vault sub-folders created by ``sync_structure``; the sync map may add more.
STRUCTURE_FOLDER_MAPPING: dict[str, str] = {
    "docs/brainstorming": "Brainstorming",
    "docs/plans": "Plans",
    "docs/blueprints": "Blueprints",
    "docs/adr": "ADR",
    "docs/releases": "Releases",
    ".agents/memory": "Memory",
    "lessons": "Lessons",
    "patterns": "Patterns",
}
# Built rather than written literally so the module can be embedded in Markdown
# code blocks without closing them early.
_FENCE = "`" * 3
_BASE_SUBDIRS: tuple[str, ...] = ("Assets", "Indexes")
# Matches both the plain "Project Slug: x" form and the generated "**Project Slug**: x".
_README_SLUG_PATTERN: re.Pattern[str] = re.compile(r"Project Slug(?:\*\*)?:\s*([^\n\r]+)")


def _now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat()


def _read_json(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cast(dict[str, Any], data) if isinstance(data, dict) else {}
    except Exception:
        return {}


def _find_git_root(project_root: str) -> str | None:
    # Filesystem walk instead of `git rev-parse`: subprocesses are gated by the
    # workflow test enforcer when called outside the CLI (e.g. KnowledgeAPI.sync).
    current = os.path.abspath(project_root)
    while True:
        if os.path.exists(os.path.join(current, ".git")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def resolve_project_id(project_root: str) -> str:
    """project_id from project config, then project profile, then git root name, then dir name."""
    project_id = str(load_project_config(project_root).get("project_id", "") or "")
    if not project_id:
        prof = _read_json(os.path.join(project_root, ".agents", "project-profile.json"))
        project_id = str(prof.get("name", "") or prof.get("id", "") or "")
    if not project_id:
        git_root = _find_git_root(project_root)
        project_id = os.path.basename(git_root) if git_root else ""
    return project_id or os.path.basename(os.path.abspath(project_root))


def make_project_slug(project_id: str) -> str:
    """Title-case each segment of a sanitized id, keeping AI/AIWF upper-case (e.g. my_project -> My_Project)."""
    clean_id = re.sub(r"[^a-zA-Z0-9\-_.]", "", project_id.replace(" ", "-"))
    clean_id = re.sub(r"_+", "_", re.sub(r"-+", "-", clean_id)).strip("-").strip("_")
    formatted: list[str] = []
    for part in re.split(r"([\-_.])", clean_id):
        if part in ("-", "_", "."):
            formatted.append(part)
        elif part.lower() in ("ai", "aiwf"):
            formatted.append(part.upper())
        else:
            formatted.append(part.capitalize())
    return "".join(formatted)


def _vault_root(obs_cfg: dict[str, Any]) -> str:
    vault_root = str(obs_cfg.get("vault_root", "") or "")
    vault_path = str(obs_cfg.get("vault_path", "") or "")
    if vault_path and not vault_root:
        vault_root = vault_path
        warnings.warn("Obsidian Configuration Warning: 'vault_path' is deprecated. Please migrate to 'vault_root'.")
    if not vault_root:
        raise ValueError("Obsidian vault_root is empty or not configured.")
    return os.path.abspath(os.path.expanduser(vault_root))


def _vault_folder(obs_cfg: dict[str, Any], mapping: dict[str, Any], project_slug: str) -> str:
    if mapping:
        return str(mapping.get("vault_folder", ""))
    pattern = str(obs_cfg.get("project_folder_pattern", DEFAULT_FOLDER_PATTERN))
    vault_folder = pattern.replace("{project_slug}", project_slug)
    if "/" in vault_folder or "\\" in vault_folder or ".." in vault_folder:
        raise ValueError(f"Path traversal detected in project_folder_pattern or resolved vault_folder: {vault_folder}")
    return vault_folder


def _assert_inside_vault(vault_root: str, resolved_path: str) -> None:
    try:
        inside = os.path.commonpath([vault_root, resolved_path]) == vault_root
    except ValueError as e:
        raise ValueError(f"Security Violation: Path validation failed: {e}") from e
    if not inside:
        raise ValueError("Security Violation: Resolved Obsidian path must be inside vault_root.")


def _assert_not_foreign(resolved_path: str, vault_folder: str, project_slug: str) -> None:
    readme_path = os.path.join(resolved_path, "README.md")
    if not os.path.exists(readme_path):
        return
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            match = _README_SLUG_PATTERN.search(f.read())
    except OSError:
        return
    if match:
        existing_slug = match.group(1).strip()
        if existing_slug != project_slug:
            raise ValueError(
                f"Conflict: Obsidian folder '{vault_folder}' belongs to another project (slug: {existing_slug})."
            )


def _render_readme(obs_cfg: dict[str, Any], project_root: str, project_id: str, project_slug: str) -> str:
    links = "\n".join(f"- [[{name}/README|{name}]]" for name in (
        "Brainstorming", "Plans", "Blueprints", "ADR", "Memory", "Releases", "Lessons", "Patterns"))
    return f"""# Obsidian Knowledge Vault - {project_id}

This is the automatically managed Obsidian knowledge folder for project **{project_id}**.

## Project Metadata
- **Project Name**: {project_id}
- **Project Slug**: {project_slug}
- **AIWF Project Path**: {os.path.abspath(project_root)}
- **Last Sync Time**: {_now_iso()}
- **Sync Mode**: {obs_cfg.get("mode", "file-sync")}

## Configuration Summary
{_FENCE}json
{json.dumps(mask_secrets(obs_cfg), indent=2)}
{_FENCE}

## Folder Structure Links
{links}
"""


def _provision_structure(resolved_path: str, obs_cfg: dict[str, Any], project_root: str,
                         project_id: str, project_slug: str) -> None:
    folder_mapping = cast(dict[str, str], obs_cfg.get("folder_mapping", STRUCTURE_FOLDER_MAPPING))
    subdirs = list(_BASE_SUBDIRS)
    subdirs += [d for d in folder_mapping.values() if d not in subdirs]
    for sub in subdirs:
        os.makedirs(os.path.join(resolved_path, sub), exist_ok=True)
    readme_path = os.path.join(resolved_path, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(_render_readme(obs_cfg, project_root, project_id, project_slug))


def resolve_obsidian_project_folder(project_root: str = ".") -> str:
    """Return the absolute vault folder for this project, creating it and its map as configured.

    Raises ValueError when Obsidian is unconfigured, the folder would escape
    ``vault_root``, or the folder's README declares a different project slug.
    """
    project_root = project_root or "."
    obs_cfg = resolve_provider_config("obsidian", project_root)
    if not obs_cfg:
        raise ValueError("Obsidian provider is not configured.")

    vault_root = _vault_root(obs_cfg)
    map_path = os.path.join(project_root, *PROJECT_MAP_RELPATH)
    project_id = resolve_project_id(project_root)
    project_slug = make_project_slug(project_id)
    mapping = _read_json(map_path)

    vault_folder = _vault_folder(obs_cfg, mapping, project_slug)
    resolved_path = os.path.abspath(os.path.join(vault_root, vault_folder))
    _assert_inside_vault(vault_root, resolved_path)
    if os.path.exists(resolved_path):
        _assert_not_foreign(resolved_path, vault_folder, project_slug)

    if not os.path.exists(resolved_path) and obs_cfg.get("create_if_missing", True):
        os.makedirs(resolved_path, exist_ok=True)
    if os.path.exists(resolved_path) and obs_cfg.get("sync_structure", True):
        _provision_structure(resolved_path, obs_cfg, project_root, project_id, project_slug)

    now_iso = _now_iso()
    os.makedirs(os.path.dirname(map_path), exist_ok=True)
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump({
            "project_id": project_id,
            "project_slug": project_slug,
            "vault_root": vault_root,
            "vault_folder": vault_folder,
            "resolved_path": resolved_path,
            "created_at": mapping.get("created_at", now_iso),
            "updated_at": now_iso,
        }, f, indent=2)
    return resolved_path


__all__ = [
    "DEFAULT_FOLDER_PATTERN",
    "PROJECT_MAP_RELPATH",
    "STRUCTURE_FOLDER_MAPPING",
    "make_project_slug",
    "resolve_obsidian_project_folder",
    "resolve_project_id",
]
