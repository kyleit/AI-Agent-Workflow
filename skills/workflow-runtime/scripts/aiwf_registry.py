import os
import sys
import json
import hashlib
import platform
import shutil
from pathlib import Path
from datetime import datetime

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

def load_registry() -> dict:
    """Load registry file, handling corrupted formats via automatic backup recovery."""
    path = get_registry_path()
    default_registry = {
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
            return data
    except Exception as e:
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

def save_registry_atomic(data: dict) -> None:
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
    except Exception as e:
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise IOError(f"Failed to write registry atomically: {e}")

def is_aiwf_installed(project_path: Path) -> bool:
    """Validate that the target path contains a valid AIWF setup."""
    agents_dir = project_path / ".agents"
    return (
        agents_dir.exists() and
        (agents_dir / "AI_RULES.md").exists() and
        (agents_dir / "skills").exists()
    )

def register_project(project_path: str, force: bool = False, source: str = "register", framework_root: str = None) -> dict:
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
    for p in registry["projects"]:
        if p["id"] == proj_id or normalize_path(p["path"]) == norm_path:
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
            
    now_str = datetime.now().astimezone().isoformat()
    
    if existing:
        existing["path"] = str(norm_path) # Update to standardized path string
        existing["last_seen_at"] = now_str
        existing["aiwf_version"] = version
        existing["status"] = "active"
        if source == "install":
            existing["last_installed_at"] = now_str
    else:
        new_project = {
            "id": proj_id,
            "path": str(norm_path),
            "name": norm_path.name,
            "registered_at": now_str,
            "last_seen_at": now_str,
            "last_installed_at": now_str if source == "install" else None,
            "last_updated_at": None,
            "aiwf_version": version,
            "install_source": source,
            "status": "active"
        }
        registry["projects"].append(new_project)
        
    save_registry_atomic(registry)
    return {
        "status": "success", 
        "project_path": str(norm_path), 
        "registry_path": str(get_registry_path())
    }

def unregister_project(project_path: str) -> bool:
    """Remove a project from registry by path."""
    norm_path = normalize_path(project_path)
    registry = load_registry()
    proj_id = generate_project_id(norm_path)
    
    initial_len = len(registry["projects"])
    registry["projects"] = [
        p for p in registry["projects"] 
        if p["id"] != proj_id and normalize_path(p["path"]) != norm_path
    ]
    
    if len(registry["projects"]) < initial_len:
        save_registry_atomic(registry)
        return True
    return False

def list_projects() -> list:
    """Return list of all registered projects."""
    registry = load_registry()
    return registry["projects"]

def doctor_registry() -> dict:
    """Check existence and AIWF state of all registered projects."""
    registry = load_registry()
    report = {
        "registry_path": str(get_registry_path()),
        "total_registered": len(registry["projects"]),
        "active": 0,
        "missing": 0,
        "details": []
    }
    
    changed = False
    for p in registry["projects"]:
        p_path = Path(p["path"])
        p_status = "active"
        issues = []
        
        if not p_path.exists():
            p_status = "missing"
            issues.append("Project folder not found on disk")
        elif not is_aiwf_installed(p_path):
            issues.append("Missing .agents/ workspace skills installation")
            
        if p_status != p["status"]:
            p["status"] = p_status
            changed = True
            
        if p_status == "active":
            report["active"] += 1
        else:
            report["missing"] += 1
            
        report["details"].append({
            "name": p["name"],
            "path": p["path"],
            "status": p_status,
            "aiwf_version": p["aiwf_version"],
            "issues": issues
        })
        
    if changed:
        save_registry_atomic(registry)
        
    return report

def cleanup_registry() -> dict:
    """Remove all invalid or non-existent project paths from registry."""
    registry = load_registry()
    initial_len = len(registry["projects"])
    
    valid_projects = []
    removed = []
    for p in registry["projects"]:
        p_path = Path(p["path"])
        if p_path.exists():
            valid_projects.append(p)
        else:
            removed.append(p["path"])
            
    if len(valid_projects) < initial_len:
        registry["projects"] = valid_projects
        save_registry_atomic(registry)
        
    return {
        "total_removed": len(removed),
        "removed_paths": removed,
        "remaining": len(valid_projects)
    }

def update_all_projects() -> dict:
    """Update all active registered projects sequentially, handling individual errors."""
    import subprocess
    registry = load_registry()
    
    summary = {
        "total": len(registry["projects"]),
        "updated": 0,
        "skipped": 0,
        "failed": 0,
        "missing": 0,
        "details": []
    }
    
    # Locate global update.sh script relative to runtime tool path
    script_dir = Path(__file__).resolve().parent
    framework_root = registry.get("framework_root")
    if framework_root and Path(framework_root).exists():
        root_dir = Path(framework_root)
    else:
        root_dir = script_dir.parents[2] # Walk up from skills/workflow-runtime/scripts to root
        
    update_script_sh = root_dir / "update.sh"
    update_script_ps = root_dir / "update.ps1"
    
    changed = False
    for p in registry["projects"]:
        p_path = Path(p["path"])
        
        # Check path existence
        if not p_path.exists():
            p["status"] = "missing"
            changed = True
            summary["missing"] += 1
            summary["details"].append({
                "path": p["path"],
                "status": "failed",
                "reason": "Project path not found on disk"
            })
            continue
            
        # Run local script to update the target project
        success = False
        reason = ""
        system = platform.system()
        
        try:
            if system == "Windows":
                # Execute PowerShell script
                if update_script_ps.exists():
                    cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(update_script_ps), "--force"]
                    # We pass CWD as the project path because update script targets project root
                    res = subprocess.run(cmd, cwd=str(p_path), capture_output=True, text=True, check=True)
                    success = True
                else:
                    reason = "update.ps1 script not found in framework root"
            else:
                # Unix systems
                if update_script_sh.exists():
                    cmd = ["/usr/bin/env", "bash", str(update_script_sh), "--force"]
                    res = subprocess.run(cmd, cwd=str(p_path), capture_output=True, text=True, check=True)
                    success = True
                else:
                    reason = "update.sh script not found in framework root"
        except subprocess.CalledProcessError as e:
            reason = f"Update script exited with code {e.returncode}. Error: {e.stderr.strip()}"
        except Exception as e:
            reason = f"Execution error: {e}"
            
        if success:
            summary["updated"] += 1
            p["last_updated_at"] = datetime.now().astimezone().isoformat()
            p["last_seen_at"] = p["last_updated_at"]
            p["status"] = "active"
            changed = True
            summary["details"].append({
                "path": p["path"],
                "status": "success",
                "reason": "Updated successfully"
            })
        else:
            summary["failed"] += 1
            summary["details"].append({
                "path": p["path"],
                "status": "failed",
                "reason": reason
            })
            
    if changed:
        save_registry_atomic(registry)
        
    return summary
