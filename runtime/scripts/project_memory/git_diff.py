# git_diff.py
import subprocess
from common import get_project_root, to_posix_path

def is_git_available() -> bool:
    try:
        res = subprocess.run(["git", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    except Exception:
        return False

def is_git_repository(root_dir: str = None) -> bool:
    if not root_dir:
        root_dir = get_project_root()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"], 
            cwd=root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        return res.returncode == 0 and res.stdout.decode().strip() == "true"
    except Exception:
        return False

def get_changed_files(since_commit: str, root_dir: str = None) -> list[str]:
    """Lấy danh sách các tệp đã thay đổi kể từ commit hash được cung cấp."""
    if not root_dir:
        root_dir = get_project_root()
    if not is_git_repository(root_dir):
        return []
    
    try:
        # Lấy file changed giữa since_commit và HEAD
        res = subprocess.run(
            ["git", "diff", "--name-only", since_commit, "HEAD"],
            cwd=root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        files = res.stdout.decode().splitlines()
        return [to_posix_path(f.strip()) for f in files if f.strip()]
    except Exception:
        return []

def get_uncommitted_files(root_dir: str = None) -> list[str]:
    """Lấy danh sách các tệp tin chưa commit (unstaged + untracked)."""
    if not root_dir:
        root_dir = get_project_root()
    if not is_git_repository(root_dir):
        return []
    
    try:
        # Lấy unstaged/untracked files
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        lines = res.stdout.decode().splitlines()
        files = []
        for line in lines:
            if len(line) > 3:
                # Bỏ qua tiền tố trạng thái (ví dụ " M ", "?? ")
                files.append(to_posix_path(line[3:].strip()))
        return files
    except Exception:
        return []

def get_latest_commit_hash(root_dir: str = None) -> str:
    if not root_dir:
        root_dir = get_project_root()
    if not is_git_repository(root_dir):
        return ""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
        )
        return res.stdout.decode().strip()
    except Exception:
        return ""
