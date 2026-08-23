# git_diff.py
from __future__ import annotations

import subprocess

from .common import get_project_root, to_posix_path


def is_git_available() -> bool:
    try:
        res = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    except Exception:
        return False


def is_git_repository(root_dir: str | None = None) -> bool:
    base_dir = root_dir or get_project_root()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=base_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return res.returncode == 0 and res.stdout.decode().strip() == "true"
    except Exception:
        return False


def get_changed_files(since_commit: str, root_dir: str | None = None) -> list[str]:
    """Lấy danh sách các tệp đã thay đổi kể từ commit hash được cung cấp."""
    base_dir = root_dir or get_project_root()
    if not is_git_repository(base_dir):
        return []

    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", since_commit, "HEAD"],
            cwd=base_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        files = res.stdout.decode().splitlines()
        return [to_posix_path(f.strip()) for f in files if f.strip()]
    except Exception:
        return []


def get_uncommitted_files(root_dir: str | None = None) -> list[str]:
    """Lấy danh sách các tệp tin chưa commit (unstaged + untracked)."""
    base_dir = root_dir or get_project_root()
    if not is_git_repository(base_dir):
        return []

    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=base_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        lines = res.stdout.decode().splitlines()
        files: list[str] = []
        for line in lines:
            if len(line) > 3:
                files.append(to_posix_path(line[3:].strip()))
        return files
    except Exception:
        return []


def get_latest_commit_hash(root_dir: str | None = None) -> str:
    base_dir = root_dir or get_project_root()
    if not is_git_repository(base_dir):
        return ""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=base_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        return res.stdout.decode().strip()
    except Exception:
        return ""


__all__ = [
    "is_git_available",
    "is_git_repository",
    "get_changed_files",
    "get_uncommitted_files",
    "get_latest_commit_hash",
]
