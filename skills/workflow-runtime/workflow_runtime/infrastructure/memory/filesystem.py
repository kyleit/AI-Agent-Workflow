# filesystem.py
from __future__ import annotations

import os
from datetime import datetime

from .common import get_project_root, to_posix_path

IGNORE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env", ".pytest_cache",
    ".vscode", ".agents", "public_export", "dist", "out", "build",
    "__pycache__", "tmp", "temp"
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db", "package-lock.json", "yarn.lock", "pnpm-lock.yaml"
}


def get_project_files(root_dir: str | None = None) -> list[str]:
    """Trả về danh sách các tệp tin trong dự án (đã lọc các tệp/thư mục cần ignore). Path tương đối."""
    base_dir = root_dir or get_project_root()
    project_files: list[str] = []

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in IGNORE_FILES:
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, base_dir)
            project_files.append(to_posix_path(rel_path))

    return project_files


def get_file_timestamp(rel_path: str, root_dir: str | None = None) -> float:
    base_dir = root_dir or get_project_root()
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        return os.path.getmtime(full_path)
    return 0.0


def get_changed_files_by_timestamp(since_timestamp_iso: str, root_dir: str | None = None) -> list[str]:
    """Tìm các tệp tin sửa đổi dựa trên thời gian sửa đổi (filesystem timestamp fallback)."""
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


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


__all__ = [
    "IGNORE_DIRS",
    "IGNORE_FILES",
    "get_project_files",
    "get_file_timestamp",
    "get_changed_files_by_timestamp",
    "ensure_directory",
]
