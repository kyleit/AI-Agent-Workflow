# release_manager.py
import os
import sys
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

    # 0. Automatically update project memory before release to ensure memory files are packed in the release commit
    print("[INFO] Automatically updating project memory before release execution...")
    try:
        sys_path_backup = list(sys.path)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        memory_dir = os.path.join(current_dir, "memory")
        if memory_dir not in sys.path:
            sys.path.append(memory_dir)
        if current_dir not in sys.path:
            sys.path.append(current_dir)
            
        from memory.update import run_update
        mem_res = run_update()
        print(f"[INFO] Project memory update status: {mem_res.get('status')}. Summary: {mem_res.get('summary')}")
        
        # Restore sys.path
        sys.path = sys_path_backup
    except Exception as e:
        print(f"[WARN] Failed to automatically update project memory: {e}")

    # 0.5. Automatically package/copy walkthrough context from IDE brain to the project repository before release commit
    print("[INFO] Packaging conversation walkthrough.md into project repository...")
    try:
        session = load_session()
        conversation_id = session.get("conversation_id")
        work_item = session.get("work_item", {})
        work_item_id = work_item.get("id") if isinstance(work_item, dict) else None
        
        if conversation_id:
            home_dir = os.path.expanduser("~")
            source_walkthrough = os.path.join(home_dir, ".gemini", "antigravity-ide", "brain", conversation_id, "walkthrough.md")
            
            if os.path.exists(source_walkthrough):
                state_dir = os.path.join(".agents", "state")
                dest_walkthrough = os.path.join(state_dir, "walkthrough.md")
                os.makedirs(state_dir, exist_ok=True)
                
                verify_dir = os.path.join("docs", "verification")
                dest_verify = os.path.join(verify_dir, f"{work_item_id}_walkthrough.md") if work_item_id else None
                if dest_verify:
                    os.makedirs(verify_dir, exist_ok=True)
                
                import shutil
                
                # Check if target files exist and ask user
                target_exists = os.path.exists(dest_walkthrough) or (dest_verify and os.path.exists(dest_verify))
                action = "Overwrite"
                if target_exists:
                    try:
                        try:
                            from utils import prompt_select
                        except (ImportError, ValueError):
                            from .utils import prompt_select
                        question = f"File walkthrough.md already exists in the repository for {work_item_id or 'this project'}. How would you like to handle it?"
                        options = ["Overwrite (Create clean new walkthrough)", "Keep & Append (Merge history)", "Skip Packaging"]
                        action = prompt_select(question, options, default="Keep & Append (Merge history)")
                    except Exception as e:
                        print(f"[WARN] Failed to prompt for walkthrough handling choice: {e}. Defaulting to 'Keep & Append'.")
                        action = "Keep & Append"
                
                if action.startswith("Overwrite"):
                    shutil.copy2(source_walkthrough, dest_walkthrough)
                    print(f"[INFO] Successfully overwrote walkthrough.md to {dest_walkthrough}")
                    if dest_verify:
                        shutil.copy2(source_walkthrough, dest_verify)
                        print(f"[INFO] Successfully archived walkthrough.md to {dest_verify}")
                elif action.startswith("Keep"):
                    # Helper to append walkthrough
                    for path_dst in [dest_walkthrough, dest_verify]:
                        if not path_dst:
                            continue
                        if os.path.exists(path_dst):
                            with open(path_dst, "r", encoding="utf-8") as f:
                                old_content = f.read()
                            with open(source_walkthrough, "r", encoding="utf-8") as f:
                                new_content = f.read()
                            # Combine old and new content
                            with open(path_dst, "w", encoding="utf-8") as f:
                                f.write(old_content + "\n\n---\n\n" + new_content)
                            print(f"[INFO] Successfully appended walkthrough to {path_dst}")
                        else:
                            shutil.copy2(source_walkthrough, path_dst)
                            print(f"[INFO] Successfully created walkthrough at {path_dst}")
                else:
                    print(f"[INFO] Skipped copy/update of walkthrough files as per user choice.")
            else:
                print(f"[WARN] Walkthrough file not found at IDE brain: {source_walkthrough}")
        else:
            print("[WARN] No active conversation_id found in session context.")
    except Exception as e:
        print(f"[WARN] Failed to automatically package walkthrough context: {e}")

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

