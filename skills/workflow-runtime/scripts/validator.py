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
    
    # 1. Check MANIFEST.json in current directory
    if os.path.exists("MANIFEST.json"):
        try:
            with open("MANIFEST.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                info["version"] = data.get("version", "0.0.0")
                info["source"] = "MANIFEST.json"
                return info
        except (json.JSONDecodeError, IOError):
            pass
            
    # 2. Check .agents/MANIFEST.json (installed framework location)
    agents_manifest = os.path.join(".agents", "MANIFEST.json")
    if os.path.exists(agents_manifest):
        try:
            with open(agents_manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
                info["version"] = data.get("version", "0.0.0")
                info["source"] = ".agents/MANIFEST.json"
                return info
        except (json.JSONDecodeError, IOError):
            pass
            
    # 3. Fallback to Git Tag if available
    try:
        res = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        tag = res.stdout.strip()
        if tag:
            # Strip leading 'v' if present
            version = tag[1:] if tag.startswith('v') else tag
            info["version"] = version
            info["source"] = "git tag"
            return info
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
        
    return info

