import os
import subprocess
import hashlib

def get_git_remote(cwd: str) -> str:
    try:
        res = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=cwd, capture_output=True, text=True, check=True
        )
        return res.stdout.strip()
    except Exception:
        return "none"

def get_manifest_size(cwd: str) -> int:
    manifest_path = os.path.join(cwd, "MANIFEST.json")
    if os.path.exists(manifest_path):
        try:
            return os.path.getsize(manifest_path)
        except Exception:
            return 0
    manifest_path_agents = os.path.join(cwd, ".agents", "MANIFEST.json")
    if os.path.exists(manifest_path_agents):
        try:
            return os.path.getsize(manifest_path_agents)
        except Exception:
            return 0
    return 0

def calculate_project_fingerprint(root_path: str) -> str:
    root_path_abs = os.path.abspath(root_path)
    git_remote = get_git_remote(root_path_abs)
    manifest_size = get_manifest_size(root_path_abs)
    
    raw_str = f"{root_path_abs}|{git_remote}|{manifest_size}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
