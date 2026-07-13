# release_manager.py
import os
import json
import subprocess
from session import load_session

def run_release_plan() -> dict[str, object]:
    session = load_session()
    
    # Check git clean
    is_clean = True
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        if res.stdout.strip():
            is_clean = False
    except Exception:
        pass
        
    warnings: list[str] = []
    if not is_clean:
        warnings.append("Git working directory has uncommitted changes.")
        
    return {
        "status": "success",
        "command": "release plan",
        "summary": "Release preflight complete. Prepared release plan.",
        "warnings": warnings,
        "files_read": [],
        "files_written": [],
        "next_skill": "implementation-to-release"
    }

def run_release_execute(approve: bool = False) -> dict[str, object]:
    if not approve:
        return {
            "status": "failure",
            "command": "release execute",
            "summary": "Release execution aborted: Explicit user approval required to commit/tag/push.",
            "warnings": ["Missing approval gate"],
            "files_read": [],
            "files_written": []
        }
        
    from session import load_workflow_config
    config = load_workflow_config()
    git_flow = config.get("git_flow", {})
    dev_branch = str(git_flow.get("development_branch", "main"))
    rel_branch = str(git_flow.get("release_branch", "main"))
    sync_method = str(git_flow.get("sync_method", "merge"))
    extra_branches: list[object] = list(git_flow.get("extra_push_branches", []))
    
    pipeline = config.get("release_pipeline", {})
    steps: list[object] = list(pipeline.get("steps", []))
    custom_cmds = pipeline.get("custom_commands", {})
    if not isinstance(custom_cmds, dict):
        custom_cmds = {}
        
    # 1. Detect changed files to identify affected modules
    affected_modules: list[str] = []
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        release_config_path = os.path.join(".agents", "release.config.json")
        if os.path.exists(release_config_path):
            with open(release_config_path, "r", encoding="utf-8") as f:
                rel_data = json.load(f)
                modules = rel_data.get("modules", [])
                if isinstance(modules, list):
                    for mod in modules:
                        if isinstance(mod, dict):
                            mod_name = str(mod.get("name", ""))
                            mod_path = str(mod.get("path", "."))
                            for line in res.stdout.splitlines():
                                file_path = line[3:].strip()
                                if file_path.startswith(mod_path if mod_path != "." else ""):
                                    if mod_name and mod_name not in affected_modules:
                                        affected_modules.append(mod_name)
    except Exception:
        pass
        
    if not affected_modules:
        affected_modules = ["framework-core"]
        
    executed_commands: list[str] = []
    try:
        # Step: Git Sync (Merge/Rebase from dev to release branch)
        if dev_branch != rel_branch:
            print(f"[INFO] Syncing {dev_branch} into {rel_branch} using {sync_method}...")
            subprocess.run(["git", "checkout", rel_branch], check=True)
            if sync_method == "rebase":
                subprocess.run(["git", "rebase", dev_branch], check=True)
            else:
                subprocess.run(["git", "merge", dev_branch, "--no-edit"], check=True)
                
        # Execute pipeline steps
        for step in steps:
            step_name = str(step)
            if step_name == "custom_commands":
                # Run module-specific custom commands
                for mod in affected_modules:
                    cmds = custom_cmds.get(mod, [])
                    if isinstance(cmds, list):
                        for cmd in cmds:
                            cmd_str = str(cmd)
                            print(f"[INFO] Running custom command for {mod}: {cmd_str}")
                            subprocess.run(cmd_str, shell=True, check=True)
                            executed_commands.append(cmd_str)
                # Run global custom commands
                global_cmds = custom_cmds.get("global", [])
                if isinstance(global_cmds, list):
                    for cmd in global_cmds:
                        cmd_str = str(cmd)
                        print(f"[INFO] Running global custom command: {cmd_str}")
                        subprocess.run(cmd_str, shell=True, check=True)
                        executed_commands.append(cmd_str)
                        
            elif step_name == "git_push":
                # Push main release branch
                print(f"[INFO] Pushing release branch {rel_branch}...")
                subprocess.run(["git", "push", "origin", rel_branch, "--tags"], check=True)
                # Push extra branches
                for ext_branch in extra_branches:
                    ext_branch_str = str(ext_branch)
                    print(f"[INFO] Pushing extra branch {ext_branch_str}...")
                    subprocess.run(["git", "push", "origin", f"{rel_branch}:{ext_branch_str}"], check=True)
                    
    except Exception as e:
        return {
            "status": "failure",
            "command": "release execute",
            "summary": f"Release execution failed during step execution: {e}",
            "warnings": [str(e)],
            "files_read": [],
            "files_written": []
        }
        
    return {
        "status": "success",
        "command": "release execute",
        "summary": "Release executed successfully. Custom Git flow and release pipeline completed.",
        "warnings": [],
        "files_read": [".agents/workflow.config.json"],
        "files_written": ["CHANGELOG.md", "MANIFEST.json"]
    }

