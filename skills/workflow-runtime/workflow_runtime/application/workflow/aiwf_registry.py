from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, cast

SCHEMA_VERSION = 1

def get_registry_dir() -> Path:
    """Determine OS-specific configuration directory for registry."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "aiwf"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "aiwf"

    # Linux and fallback
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "aiwf"
    return Path.home() / ".config" / "aiwf"

def get_registry_path() -> Path:
    """Return the absolute path to projects.json registry."""
    # Hard fallback to home if AppData folder cannot be created
    try:
        registry_dir = get_registry_dir()
        registry_dir.mkdir(parents=True, exist_ok=True)
        return registry_dir / "projects.json"
    except Exception:
        fallback_dir = Path.home() / ".aiwf"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        return fallback_dir / "projects.json"

def normalize_path(project_path: str) -> Path:
    """Normalize absolute path. Case-insensitive comparison on Windows."""
    abs_path = Path(project_path).resolve()
    if platform.system() == "Windows":
        # Lowercase drive letter and path for case-insensitive matching on Windows
        return Path(str(abs_path).lower())
    return abs_path

def generate_project_id(normalized_path: Path) -> str:
    """Generate a stable MD5 hash representing the normalized project path."""
    return hashlib.md5(str(normalized_path).encode("utf-8")).hexdigest()

def load_registry() -> dict[str, Any]:
    """Load registry file, handling corrupted formats via automatic backup recovery."""
    path = get_registry_path()
    default_registry: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "updated_at": datetime.now().astimezone().isoformat(),
        "framework_root": None,
        "projects": []
    }

    if not path.exists():
        return default_registry

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "projects" not in data:
                raise ValueError("Invalid registry structure")
            return cast(dict[str, Any], data)
    except Exception:
        # File is corrupted, backup and recreate
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_path = path.with_name(f"projects.json.bak.{timestamp}")
        try:
            shutil.copy2(path, backup_path)
            print(f"[WARN] Registry file was corrupted. Backed up to: {backup_path}")
        except Exception:
            print("[WARN] Registry file was corrupted and backup failed.")

        # Save fresh default registry
        save_registry_atomic(default_registry)
        return default_registry

def save_registry_atomic(data: dict[str, Any]) -> None:
    """Save registry data using atomic write patterns (write tmp, rename) to avoid half-written corruption."""
    path = get_registry_path()
    temp_path = path.with_name("projects.json.tmp")
    data["updated_at"] = datetime.now().astimezone().isoformat()

    try:
        # Write to temp file
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace
        if temp_path.exists():
            os.replace(temp_path, path)
    except Exception as exc:
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise IOError(f"Failed to write registry atomically: {exc}")

def is_aiwf_installed(project_path: Path) -> bool:
    """Validate that the target path contains a valid AIWF setup."""
    agents_dir = project_path / ".agents"
    return (
        agents_dir.exists() and
        (agents_dir / "AI_RULES.md").exists() and
        (agents_dir / "skills").exists()
    )

def read_installed_aiwf_version(project_path: Path) -> str:
    """Read installed AIWF version from a project, returning 'unknown' on any problem."""
    manifest_path = project_path / ".agents" / "MANIFEST.json"
    if not manifest_path.exists():
        return "unknown"
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return str(manifest.get("version") or "unknown")
    except Exception:
        return "unknown"

def normalize_project_record(project: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Backfill fields added after early registry versions without crashing doctor/list."""
    changed = False
    normalized = dict(project)
    raw_path = str(normalized.get("path") or ".")
    norm_path = normalize_path(raw_path)
    now_str = datetime.now().astimezone().isoformat()
    defaults = {
        "id": generate_project_id(norm_path),
        "path": str(norm_path),
        "name": norm_path.name or "project",
        "registered_at": now_str,
        "last_seen_at": None,
        "last_installed_at": None,
        "last_updated_at": None,
        "aiwf_version": read_installed_aiwf_version(Path(raw_path)),
        "install_source": "legacy",
        "telegram_chat_id": None,
        "status": "active" if Path(raw_path).exists() else "missing",
    }
    for key, value in defaults.items():
        if key not in normalized:
            normalized[key] = value
            changed = True
    return normalized, changed

def register_project(project_path: str, force: bool = False, source: str = "register", framework_root: str | None = None) -> dict[str, Any]:
    """Register a project path. Updates seen tags if already registered."""
    norm_path = normalize_path(project_path)
    if not norm_path.exists():
        return {"status": "error", "message": f"Path does not exist: {project_path}"}

    if not force and not is_aiwf_installed(norm_path):
        return {
            "status": "error",
            "message": "This project does not appear to have AIWF installed (missing .agents/). Run: aiwf install first or use --force."
        }

    registry = load_registry()
    if framework_root:
        registry["framework_root"] = str(normalize_path(framework_root))

    proj_id = generate_project_id(norm_path)

    # Find existing project
    existing = None
    registry["projects"] = [normalize_project_record(p)[0] for p in cast(list[dict[str, Any]], registry.get("projects", []))]
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    for p in projects_list:
        normalized, _changed = normalize_project_record(p)
        if normalized.get("id") == proj_id or normalize_path(normalized.get("path", ".")) == norm_path:
            existing = p
            break

    # Read version if MANIFEST exists
    version = "unknown"
    manifest_path = norm_path / ".agents" / "MANIFEST.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                version = manifest.get("version", "unknown")
        except Exception:
            pass
    # Read TELEGRAM_CHAT_ID if config exists
    chat_id = None
    env_path = norm_path / ".agents" / "config" / ".env.telegram-notify"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("TELEGRAM_CHAT_ID="):
                        chat_id = line.split("=", 1)[1].strip().strip('"').strip("'")
        except Exception:
            pass

    now_str = datetime.now().astimezone().isoformat()

    if existing:
        existing["path"] = str(norm_path) # Update to standardized path string
        existing["last_seen_at"] = now_str
        existing["aiwf_version"] = version
        existing["status"] = "active"
        if chat_id:
            existing["telegram_chat_id"] = chat_id
        if source == "install":
            existing["last_installed_at"] = now_str
    else:
        new_project: dict[str, Any] = {
            "id": proj_id,
            "path": str(norm_path),
            "name": norm_path.name,
            "registered_at": now_str,
            "last_seen_at": now_str,
            "last_installed_at": now_str if source == "install" else None,
            "last_updated_at": None,
            "aiwf_version": version,
            "install_source": source,
            "telegram_chat_id": chat_id,
            "status": "active"
        }
        projects_list.append(new_project)

    save_registry_atomic(registry)
    return {
        "status": "success",
        "project_path": str(norm_path),
        "registry_path": str(get_registry_path())
    }

def update_project_telegram_chat_id(project_path: str, chat_id: str) -> bool:
    """Explicitly update the telegram_chat_id mapping for a project path."""
    norm_path = normalize_path(project_path)
    registry = load_registry()
    proj_id = generate_project_id(norm_path)

    updated = False
    projects: list[dict[str, Any]] = []
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    for p in projects_list:
        p, _record_changed = normalize_project_record(p)
        if p.get("id") == proj_id or normalize_path(str(p.get("path", "."))) == norm_path:
            p["telegram_chat_id"] = chat_id
            updated = True
        projects.append(p)

    if updated:
        registry["projects"] = projects
        save_registry_atomic(registry)
        return True
    return False

def unregister_project(project_path: str) -> bool:
    """Remove a project from registry by path."""
    norm_path = normalize_path(project_path)
    registry = load_registry()
    proj_id = generate_project_id(norm_path)

    initial_len = len(registry["projects"])
    remaining_projects: list[dict[str, Any]] = []
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    for p in projects_list:
        p, _record_changed = normalize_project_record(p)
        if p.get("id") == proj_id or normalize_path(str(p.get("path", "."))) == norm_path:
            continue
        remaining_projects.append(p)
    registry["projects"] = remaining_projects

    if len(registry["projects"]) < initial_len:
        save_registry_atomic(registry)
        return True
    return False

def list_projects() -> list[dict[str, Any]]:
    """Return list of all registered projects."""
    registry = load_registry()
    projects: list[dict[str, Any]] = []
    changed = False
    projects_list = cast(list[dict[str, Any]], registry.get("projects", []))
    for p in projects_list:
        normalized, record_changed = normalize_project_record(p)
        projects.append(normalized)
        changed = changed or record_changed
    if changed:
        registry["projects"] = projects
        save_registry_atomic(registry)
    return projects

# --- Re-exports for backward compatibility ---
from workflow_runtime.application.workflow.registry_operations import (  # noqa: E402
    cleanup_registry,
    doctor_registry,
    update_all_projects,
)

__all__ = [
    "SCHEMA_VERSION",
    "get_registry_dir",
    "get_registry_path",
    "normalize_path",
    "generate_project_id",
    "load_registry",
    "save_registry_atomic",
    "is_aiwf_installed",
    "read_installed_aiwf_version",
    "normalize_project_record",
    "register_project",
    "update_project_telegram_chat_id",
    "unregister_project",
    "list_projects",
    "doctor_registry",
    "cleanup_registry",
    "update_all_projects",
]

