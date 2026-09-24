"""File-level sync between project docs and the project's Obsidian vault folder.

Modes: ``file-sync``/``rest`` push AIWF -> Obsidian, ``readonly`` only reports
pending pushes, ``bidirectional`` pushes or pulls whichever side changed since
the last sync and records a conflict report when both did.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
from typing import Any, cast

from workflow_runtime.application.knowledge.link_translator import (
    extract_frontmatter, translate_links_to_wikilinks,
    translate_wikilinks_to_markdown)
from workflow_runtime.infrastructure.knowledge.provider_manager.config import \
    resolve_provider_config
from workflow_runtime.infrastructure.knowledge.provider_manager.obsidian_folder import \
    resolve_obsidian_project_folder

SYNC_FOLDER_MAPPING: dict[str, str] = {
    "docs/brainstorming": "Brainstorming",
    "docs/plans": "Plans",
    "docs/quick": "Brainstorming",
    "docs/issues": "Plans",
    "docs/blueprints": "Blueprints",
    "docs/adr": "ADR",
    "docs/releases": "Releases",
    ".agents/memory": "Memory",
    "lessons": "Lessons",
    "patterns": "Patterns",
    "docs/prompts": "Prompts",
    "docs/verification": "Verification",
    "docs/debug": "Debug",
    "docs/archive": "Archive",
}
SYNC_MAP_RELPATH: tuple[str, str, str] = (".agents", "knowledge", "obsidian-sync-map.json")
CONFLICTS_RELPATH: tuple[str, str, str] = (".agents", "knowledge", "conflicts")
_SYNC_FRONTMATTER_KEYS: tuple[str, ...] = ("sync_date", "source_path", "type")


def _parse_frontmatter(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
    return fields


def _render_frontmatter(fields: dict[str, str]) -> str:
    return "---\n" + "".join(f"{k}: {v}\n" for k, v in fields.items()) + "---\n"


def merge_frontmatter(content: str, metadata: dict[str, Any]) -> str:
    """Inject or merge flat YAML frontmatter fields at the top of markdown content."""
    block, body = extract_frontmatter(content)
    fields = _parse_frontmatter(block) if block is not None else {}
    fields.update({k: str(v) for k, v in metadata.items()})
    return _render_frontmatter(fields) + (body if block is not None else content)


def clean_frontmatter(content: str) -> str:
    """Remove only the sync-added frontmatter fields, keeping the rest."""
    block, body = extract_frontmatter(content)
    if block is None:
        return content
    fields = _parse_frontmatter(block)
    for key in _SYNC_FRONTMATTER_KEYS:
        fields.pop(key, None)
    return _render_frontmatter(fields) + body if fields else body


def get_file_hash(path: str) -> str:
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except OSError:
        return ""


def _push(aiwf_file: str, obs_file: str, rel_aiwf: str, obs_folder: str, now_iso: str) -> None:
    os.makedirs(os.path.dirname(obs_file), exist_ok=True)
    if not aiwf_file.endswith(".md"):
        shutil.copy2(aiwf_file, obs_file)
        return
    with open(aiwf_file, "r", encoding="utf-8") as f:
        content = translate_links_to_wikilinks(f.read())
    meta = {"sync_date": now_iso, "source_path": rel_aiwf.replace(os.sep, "/"), "type": obs_folder.lower()}
    with open(obs_file, "w", encoding="utf-8") as f:
        f.write(merge_frontmatter(content, meta))


def _pull(obs_file: str, aiwf_file: str) -> None:
    os.makedirs(os.path.dirname(aiwf_file), exist_ok=True)
    if not obs_file.endswith(".md"):
        shutil.copy2(obs_file, aiwf_file)
        return
    with open(obs_file, "r", encoding="utf-8") as f:
        content = clean_frontmatter(translate_wikilinks_to_markdown(f.read()))
    with open(aiwf_file, "w", encoding="utf-8") as f:
        f.write(content)


def _write_conflict(project_root: str, entry: dict[str, Any], aiwf_hash: str, obs_hash: str, now_iso: str) -> None:
    conflict_dir = os.path.join(project_root, *CONFLICTS_RELPATH)
    os.makedirs(conflict_dir, exist_ok=True)
    name = entry["aiwf_path"].replace("/", "_").replace("\\", "_") + ".json"
    report = {
        "aiwf_path": entry["aiwf_path"],
        "obsidian_path": entry["obsidian_path"],
        "last_synced_at": entry.get("last_synced_at", ""),
        "aiwf_current_hash": aiwf_hash,
        "obsidian_current_hash": obs_hash,
        "detected_at": now_iso,
    }
    try:
        with open(os.path.join(conflict_dir, name), "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
    except OSError:
        pass


def _sync_file(mode: str, project_root: str, aiwf_file: str, obs_file: str, obs_folder: str,
               entry: dict[str, Any], stats: dict[str, list[str]], now_iso: str) -> dict[str, Any] | None:
    """Sync one file; return the updated sync-map entry, or None if nothing was synced."""
    rel_aiwf = cast(str, entry["aiwf_path"])
    aiwf_hash = get_file_hash(aiwf_file)
    obs_exists = os.path.exists(obs_file)
    obs_hash = get_file_hash(obs_file) if obs_exists else ""
    aiwf_changed = aiwf_hash != entry.get("last_aiwf_hash", "")
    obs_changed = obs_exists and obs_hash != entry.get("last_obsidian_hash", "")

    if mode == "readonly":
        if aiwf_changed:
            stats["skipped_readonly"].append(rel_aiwf)
        return None

    if mode == "bidirectional" and aiwf_changed and obs_changed:
        stats["conflicts"].append(rel_aiwf)
        _write_conflict(project_root, entry, aiwf_hash, obs_hash, now_iso)
        return None

    if mode in ("file-sync", "rest"):
        push, pull = aiwf_changed or not obs_exists, False
    elif mode == "bidirectional":
        push, pull = aiwf_changed, obs_changed
    else:
        return None
    try:
        if push:
            _push(aiwf_file, obs_file, rel_aiwf, obs_folder, now_iso)
            obs_hash = get_file_hash(obs_file)
            stats["copied_to_obsidian"].append(rel_aiwf)
        elif pull:
            _pull(obs_file, aiwf_file)
            aiwf_hash = get_file_hash(aiwf_file)
            stats["copied_to_aiwf"].append(rel_aiwf)
        else:
            return None
    except Exception as e:
        direction = f"copy {rel_aiwf} to Obsidian" if push else f"copy {entry['obsidian_path']} from Obsidian"
        stats["errors"].append(f"Failed to {direction}: {e}")
        return None
    return {**entry, "last_aiwf_hash": aiwf_hash, "last_obsidian_hash": obs_hash, "last_synced_at": now_iso}


def sync_obsidian(project_root: str = ".") -> dict[str, Any]:
    """Sync mapped project folders with the project's Obsidian vault folder."""
    project_root = project_root or "."
    obs_cfg = resolve_provider_config("obsidian", project_root)
    if not obs_cfg:
        return {"status": "failure", "message": "Obsidian is not configured."}
    if not obs_cfg.get("enabled", False):
        return {"status": "failure", "message": "Obsidian provider is disabled."}
    mode = str(obs_cfg.get("mode", "file-sync"))
    try:
        resolved_path = resolve_obsidian_project_folder(project_root)
    except Exception as e:
        return {"status": "failure", "message": f"Folder resolution failed: {e}"}

    folder_mapping = cast(dict[str, str], obs_cfg.get("folder_mapping", SYNC_FOLDER_MAPPING))
    sync_map_path = os.path.join(project_root, *SYNC_MAP_RELPATH)
    sync_map: dict[str, Any] = {}
    if os.path.exists(sync_map_path):
        try:
            with open(sync_map_path, "r", encoding="utf-8") as f:
                sync_map = json.load(f)
        except Exception:
            pass

    stats: dict[str, list[str]] = {
        "copied_to_obsidian": [], "copied_to_aiwf": [], "skipped_readonly": [], "conflicts": [], "errors": [],
    }
    now_iso = datetime.datetime.now().astimezone().isoformat()
    abs_project = os.path.abspath(project_root)
    abs_vault_folder = os.path.abspath(resolved_path)

    for aiwf_folder, obs_folder in folder_mapping.items():
        aiwf_dir = os.path.abspath(os.path.join(project_root, aiwf_folder))
        obs_dir = os.path.abspath(os.path.join(resolved_path, obs_folder))
        if not os.path.exists(aiwf_dir):
            continue
        if mode != "readonly":
            os.makedirs(obs_dir, exist_ok=True)
        for root, _, files in os.walk(aiwf_dir):
            for filename in files:
                if filename.startswith(".") or filename.endswith((".lock", "~")):
                    continue
                aiwf_file = os.path.join(root, filename)
                obs_file = os.path.join(obs_dir, os.path.relpath(aiwf_file, aiwf_dir))
                rel_aiwf = os.path.relpath(aiwf_file, abs_project)
                entry = {
                    "last_aiwf_hash": "",
                    "last_obsidian_hash": "",
                    "last_synced_at": "",
                    **sync_map.get(rel_aiwf, {}),
                    "aiwf_path": rel_aiwf,
                    "obsidian_path": os.path.relpath(obs_file, abs_vault_folder),
                }
                updated = _sync_file(mode, project_root, aiwf_file, obs_file, obs_folder, entry, stats, now_iso)
                if updated is not None:
                    sync_map[rel_aiwf] = updated

    os.makedirs(os.path.dirname(sync_map_path), exist_ok=True)
    try:
        with open(sync_map_path, "w", encoding="utf-8") as f:
            json.dump(sync_map, f, indent=2)
    except OSError:
        pass

    return {
        "status": "success",
        "message": (f"Sync completed with {len(stats['copied_to_obsidian'])} copied to Obsidian, "
                    f"{len(stats['copied_to_aiwf'])} copied to AIWF, {len(stats['conflicts'])} conflicts."),
        "stats": stats,
    }


__all__ = [
    "SYNC_FOLDER_MAPPING",
    "clean_frontmatter",
    "get_file_hash",
    "merge_frontmatter",
    "sync_obsidian",
]
