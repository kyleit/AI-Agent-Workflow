# filesystem.py
from __future__ import annotations

import os
from datetime import datetime

from .common import get_project_root, to_posix_path

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", ".pytest_cache",
    ".vscode", ".agents", "public_export", "dist", "out", "build",
    "__pycache__", "tmp", "temp", "_to_delete", "artifacts",
    "python-runtime-dev", ".qdrant_data", ".qmd"
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"
}


def get_project_files(root_dir: str | None = None) -> list[str]:
    """Tra ve danh sach cac tep tin trong du an (da loc cac tep/thu muc can ignore). Path tuong doi."""
    base_dir = root_dir or get_project_root()
    project_files: list[str] = []

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".tmp_")]

        for file in files:
            if file in IGNORE_FILES:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            posix_path = to_posix_path(rel_path)
            if any(posix_path.startswith(ign + "/") or f"/{ign}/" in posix_path for ign in IGNORE_DIRS):
                continue
            project_files.append(posix_path)

    return project_files


def get_file_timestamp(rel_path: str, root_dir: str | None = None) -> float:
    base_dir = root_dir or get_project_root()
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        return os.path.getmtime(full_path)
    return 0.0


def get_changed_files_by_timestamp(since_timestamp_iso: str, root_dir: str | None = None) -> list[str]:
    """Tim cac tep tin sua doi dua tren thoi gian sua doi (filesystem timestamp fallback)."""
    try:
        since_dt = datetime.fromisoformat(since_timestamp_iso)
        since_time = since_dt.timestamp()
    except Exception:
        since_time = 0.0

    changed: list[str] = []
    for file in get_project_files(root_dir):
        mtime = get_file_timestamp(file, root_dir)
        if mtime > since_time:
            changed.append(file)
    return changed
