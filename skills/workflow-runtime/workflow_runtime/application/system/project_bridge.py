"""Project-owned bridge to the global AIWF asset plane."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from workflow_runtime.application.system.global_installation.resolver import resolve_global_source


@dataclass(frozen=True)
class ProjectBridge:
    schema_version: str
    project_id: str
    canonical_root: str
    git_remote_identity: str
    bridge_mode: str
    global_installation_id: str
    global_version_policy: str
    global_version: str
    memory_namespace: str
    rag_namespace: str
    created_at: str
    last_validated_at: str


def _git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _remote_identity(root: Path) -> str:
    remote = _git(root, "config", "--get", "remote.origin.url")
    return remote.removesuffix(".git").rstrip("/").lower() if remote else f"local:{root.as_posix().lower()}"


def project_id(root: Path) -> str:
    return "PRJ-" + hashlib.sha256(_remote_identity(root).encode("utf-8")).hexdigest()[:20]


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f"{path.stem}-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def ensure_project_bridge(
    root: Path | str,
    global_root: Path | str | None = None,
    force_mode: str | None = None,
) -> ProjectBridge:
    project_root = Path(root).expanduser().resolve()
    bridge_path = project_root / ".agents" / "project.json"
    existing = _read_json(bridge_path)
    now = datetime.now(timezone.utc).isoformat()
    source = Path(global_root).expanduser().resolve() if global_root else resolve_global_source(project_root)
    has_existing_bridge = bool(existing)
    has_legacy_assets = (project_root / ".agents" / "skills").exists() or (project_root / ".agents" / "AI_RULES.md").exists()
    mode = str(existing.get("bridge_mode") or ("legacy_copy" if has_legacy_assets else "global_link"))
    if force_mode:
        mode = force_mode
    if source and source != project_root and (not has_existing_bridge and not has_legacy_assets):
        mode = "global_link"
    global_version = "unknown"
    manifest = _read_json(source / "MANIFEST.json") if source else {}
    if manifest.get("version") is not None:
        global_version = str(manifest["version"])
    pid = project_id(project_root)
    bridge = ProjectBridge(
        schema_version="aiwf.project-bridge.v1",
        project_id=pid,
        canonical_root=str(project_root),
        git_remote_identity=_remote_identity(project_root),
        bridge_mode=mode,
        global_installation_id="GLOBAL-" + hashlib.sha256(str(source or "unavailable").encode("utf-8")).hexdigest()[:16],
        global_version_policy="current",
        global_version=global_version,
        memory_namespace=f"memory:{pid}",
        rag_namespace=f"rag:{pid}",
        created_at=str(existing.get("created_at") or now),
        last_validated_at=now,
    )
    _write_json_atomic(bridge_path, asdict(bridge))
    link_payload = {
        "schema_version": "aiwf.runtime-link.v1",
        "bridge_mode": bridge.bridge_mode,
        "project_id": bridge.project_id,
        "global_installation_id": bridge.global_installation_id,
        "global_root_available": bool(source),
        "global_root": str(source) if source else None,
        "validated_at": now,
        "resolution": "global assets resolved by runtime; project assets are not copied",
    }
    _write_json_atomic(project_root / ".agents" / "runtime-link.json", link_payload)
    return bridge


def load_project_bridge(root: Path | str) -> ProjectBridge | None:
    payload = _read_json(Path(root).expanduser().resolve() / ".agents" / "project.json")
    try:
        return ProjectBridge(**{field: payload[field] for field in ProjectBridge.__dataclass_fields__})
    except (KeyError, TypeError):
        return None


def validate_project_bridge(root: Path | str) -> tuple[bool, str, ProjectBridge | None]:
    project_root = Path(root).expanduser().resolve()
    bridge = load_project_bridge(project_root)
    if bridge is None:
        return False, "PROJECT_BRIDGE_NOT_FOUND", None
    if Path(bridge.canonical_root).resolve() != project_root or bridge.project_id != project_id(project_root):
        return False, "PROJECT_IDENTITY_MISMATCH", bridge
    return True, "READY", bridge


def migrate_project_to_global(root: Path | str, global_root: Path | str | None = None) -> tuple[ProjectBridge, str]:
    """Switch an existing copy-mode project to global metadata without deleting copies."""
    project_root = Path(root).expanduser().resolve()
    source = Path(global_root).expanduser().resolve() if global_root else resolve_global_source(project_root)
    if source is None or source == project_root:
        raise ValueError("GLOBAL_INSTALLATION_UNAVAILABLE")
    bridge_path = project_root / ".agents" / "project.json"
    link_path = project_root / ".agents" / "runtime-link.json"
    backup_path = project_root / ".agents" / "state" / "recovery" / "project-bridge-before-global.json"
    if not _read_json(bridge_path):
        ensure_project_bridge(project_root, source, force_mode="legacy_copy")
    backup = {"bridge": _read_json(bridge_path), "runtime_link": _read_json(link_path), "created_at": datetime.now(timezone.utc).isoformat()}
    _write_json_atomic(backup_path, backup)
    bridge = ensure_project_bridge(project_root, source, force_mode="global_link")
    return bridge, backup_path.relative_to(project_root).as_posix()


def rollback_project_bridge(root: Path | str) -> ProjectBridge | None:
    project_root = Path(root).expanduser().resolve()
    backup_path = project_root / ".agents" / "state" / "recovery" / "project-bridge-before-global.json"
    backup = _read_json(backup_path)
    prior = backup.get("bridge")
    if not isinstance(prior, dict) or not prior:
        raise ValueError("PROJECT_BRIDGE_BACKUP_NOT_FOUND")
    _write_json_atomic(project_root / ".agents" / "project.json", prior)
    prior_link = backup.get("runtime_link")
    if isinstance(prior_link, dict) and prior_link:
        _write_json_atomic(project_root / ".agents" / "runtime-link.json", prior_link)
    return load_project_bridge(project_root)


__all__ = [
    "ProjectBridge", "ensure_project_bridge", "load_project_bridge", "migrate_project_to_global",
    "project_id", "rollback_project_bridge", "validate_project_bridge",
]
