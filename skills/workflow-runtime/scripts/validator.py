# validator.py
import os
import subprocess
import json

def get_git_info() -> dict:
    info = {
        "is_git_repository": False,
        "branch": "unknown",
        "working_tree": "clean",
        "default_branch": "main",
        "latest_tag": ""
    }
    
    # Check if git is available and is a repository
    try:
        res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        if "true" in res.stdout.strip():
            info["is_git_repository"] = True
    except (subprocess.SubprocessError, FileNotFoundError):
        return info

    if info["is_git_repository"]:
        # Get active branch
        try:
            res_branch = subprocess.run(["git", "branch", "--show-current"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            info["branch"] = res_branch.stdout.strip() or "detached"
        except subprocess.SubprocessError:
            pass
            
        # Get git status
        try:
            res_status = subprocess.run(["git", "status", "--short"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_status.stdout.strip():
                info["working_tree"] = "dirty"
        except subprocess.SubprocessError:
            pass
            
        # Get latest tag
        try:
            res_tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            info["latest_tag"] = res_tag.stdout.strip()
        except subprocess.SubprocessError:
            pass
            
    return info

def get_version_info() -> dict:
    info = {"version": "0.0.0", "source": "unknown"}
    if os.path.exists("MANIFEST.json"):
        try:
            with open("MANIFEST.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                info["version"] = data.get("version", "0.0.0")
                info["source"] = "MANIFEST.json"
        except (json.JSONDecodeError, IOError):
            pass
    return info
