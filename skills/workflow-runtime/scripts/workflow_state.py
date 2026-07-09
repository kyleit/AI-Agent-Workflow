# workflow_state.py
import os
import json
import subprocess
from datetime import datetime
from session import load_session, save_session_atomic

def get_git_status() -> dict:
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        changed = [line.strip() for line in res.stdout.splitlines() if line.strip()]
        res_branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        branch = res_branch.stdout.strip()
        return {
            "is_git": True,
            "branch": branch,
            "changed_files_count": len(changed)
        }
    except Exception:
        return {
            "is_git": False,
            "branch": "none",
            "changed_files_count": 0
        }

def init_session(permission_mode: str = "sandbox") -> dict:
    os.makedirs(".agents", exist_ok=True)
    
    # 1. Detect environment
    git_info = get_git_status()
    
    # Check if memory bootstrapped
    summary_path = os.path.join(".agents", "memory", "project-summary.md")
    memory_exists = os.path.exists(summary_path)
    
    # Check project profile
    profile_path = os.path.join(".agents", "project-profile.json")
    profile_exists = os.path.exists(profile_path)
    
    # 2. Setup session dictionary
    session = load_session()
    if not session:
        session = {}
        
    session.update({
        "checkpoint": 1,
        "current_skill": "initialize-workflow",
        "current_step": "Initialization",
        "permission_mode": permission_mode,
        "permission_mode_selected_at": datetime.now().astimezone().isoformat(),
        "permission_mode_selected_by": "user",
        "git_branch": git_info["branch"],
        "git_dirty": git_info["changed_files_count"] > 0,
        "memory_status": "bootstrapped" if memory_exists else "uninitialized",
        "project_profile_status": "exists" if profile_exists else "missing"
    })
    
    save_session_atomic(session)
    
    return {
        "status": "success",
        "command": "init",
        "summary": f"Session initialized with permission_mode={permission_mode}.",
        "warnings": [],
        "files_read": [],
        "files_written": [".agents/.session.json"],
        "next_skill": "environment-health"
    }

def resume_session() -> dict:
    session = load_session()
    if not session:
        return {
            "status": "failure",
            "command": "resume",
            "summary": "No active session found. Please run 'init' first.",
            "warnings": ["Session file missing"],
            "files_read": [],
            "files_written": [],
            "next_skill": "initialize-workflow"
        }
        
    checkpoint = session.get("checkpoint", 1)
    current_skill = session.get("current_skill", "initialize-workflow")
    
    # Sync active conversation and refresh context usage
    from context import refresh_context_usage_for_active_conversation
    refresh_context_usage_for_active_conversation(session)
    
    # Perform a light drift check by checking git branch changes
    git_info = get_git_status()
    warnings = []
    if session.get("git_branch") != git_info["branch"]:
        warnings.append(f"Git branch changed from {session.get('git_branch')} to {git_info['branch']}")
        session["git_branch"] = git_info["branch"]
    save_session_atomic(session)
        
    # Check next recommended skill based on checkpoint
    next_skill_map = {
        1: "environment-health",
        2: "project-discovery",
        3: "brainstorming",
        4: "plan-to-blueprint",
        5: "blueprint-to-implementation",
        6: "implementation-to-debug",
        7: "debug-to-verify",
        8: "implementation-to-release"
    }
    recommended_skill = next_skill_map.get(checkpoint, current_skill)
    
    return {
        "status": "success",
        "command": "resume",
        "summary": f"Resumed active workflow at checkpoint {checkpoint} (skill: {current_skill}).",
        "warnings": warnings,
        "files_read": [".agents/.session.json"],
        "files_written": [],
        "next_skill": recommended_skill
    }
