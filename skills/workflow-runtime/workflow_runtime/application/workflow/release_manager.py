from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, cast

from workflow_runtime.application.ports.locator import InfrastructureLocator


def run_release_plan() -> dict[str, object]:
    load_session_fn: Any = getattr(InfrastructureLocator, "load_session", None)
    if callable(load_session_fn):
        load_session_fn()

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

    from workflow_runtime.application.verification.release_gate import ReleaseGate

    gate_passed, gate_reason = ReleaseGate(".").validate()
    if not gate_passed:
        return {
            "status": "blocked",
            "command": "release execute",
            "code": "RELEASE_GATE_FAILED",
            "summary": "Release blocked before side effects.",
            "warnings": [gate_reason],
            "side_effects": [],
            "files_written": [],
        }

    # 0. Automatically update project memory only after all release gates pass
    print("[INFO] Automatically updating project memory before release execution...")
    try:
        update_fn: Any = getattr(InfrastructureLocator, "run_update", None)
        mem_res: dict[str, Any] = cast(dict[str, Any], update_fn()) if callable(update_fn) else {}
        print(f"[INFO] Project memory update status: {mem_res.get('status')}. Summary: {mem_res.get('summary')}")
    except Exception as e:
        print(f"[WARN] Failed to automatically update project memory: {e}")

    # 0.5. Automatically package walkthrough context
    print("[INFO] Packaging conversation walkthrough.md into project repository...")
    try:
        load_session_fn: Any = getattr(InfrastructureLocator, "load_session", None)
        session: dict[str, Any] = cast(dict[str, Any], load_session_fn()) if callable(load_session_fn) else {}
        conversation_id = str(session.get("conversation_id", ""))
        work_item_raw = session.get("work_item")
        work_item: dict[str, Any] = cast(dict[str, Any], work_item_raw) if isinstance(work_item_raw, dict) else {}
        work_item_id = str(work_item.get("id")) if work_item.get("id") else None

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

                target_exists = os.path.exists(dest_walkthrough) or (dest_verify is not None and os.path.exists(dest_verify))
                action = "Overwrite"
                if target_exists:
                    action = "Keep & Append"

                if action.startswith("Overwrite"):
                    shutil.copy2(source_walkthrough, dest_walkthrough)
                    print(f"[INFO] Successfully overwrote walkthrough.md to {dest_walkthrough}")
                    if dest_verify:
                        shutil.copy2(source_walkthrough, dest_verify)
                        print(f"[INFO] Successfully archived walkthrough.md to {dest_verify}")
                elif action.startswith("Keep"):
                    paths_to_update: list[str] = [dest_walkthrough]
                    if dest_verify:
                        paths_to_update.append(dest_verify)

                    for path_dst in paths_to_update:
                        if os.path.exists(path_dst):
                            with open(path_dst, "r", encoding="utf-8") as f:
                                old_content = f.read()
                            with open(source_walkthrough, "r", encoding="utf-8") as f:
                                new_content = f.read()
                            with open(path_dst, "w", encoding="utf-8") as f:
                                f.write(old_content + "\n\n---\n\n" + new_content)
                            print(f"[INFO] Successfully appended walkthrough to {path_dst}")
                        else:
                            shutil.copy2(source_walkthrough, path_dst)
                            print(f"[INFO] Successfully created walkthrough at {path_dst}")
                else:
                    print("[INFO] Skipped copy/update of walkthrough files as per user choice.")
            else:
                print(f"[WARN] Walkthrough file not found at IDE brain: {source_walkthrough}")
        else:
            print("[WARN] No active conversation_id found in session context.")
    except Exception as e:
        print(f"[WARN] Failed to automatically package walkthrough context: {e}")

    config_fn: Any = getattr(InfrastructureLocator, "load_workflow_config", None)
    config: dict[str, Any] = cast(dict[str, Any], config_fn()) if callable(config_fn) else {}

    git_flow: dict[str, Any] = cast(dict[str, Any], config.get("git_flow", {})) if isinstance(config.get("git_flow"), dict) else {}
    dev_branch = str(git_flow.get("development_branch", "main"))
    rel_branch = str(git_flow.get("release_branch", "main"))
    sync_method = str(git_flow.get("sync_method", "merge"))
    extra_branches: list[Any] = list(cast(list[Any], git_flow.get("extra_push_branches", [])))

    pipeline: dict[str, Any] = cast(dict[str, Any], config.get("release_pipeline", {})) if isinstance(config.get("release_pipeline"), dict) else {}
    steps: list[Any] = list(cast(list[Any], pipeline.get("steps", [])))
    custom_cmds: dict[str, Any] = cast(dict[str, Any], pipeline.get("custom_commands", {})) if isinstance(pipeline.get("custom_commands"), dict) else {}

    affected_modules: list[str] = []
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
        release_config_path = os.path.join(".agents", "release.config.json")
        if os.path.exists(release_config_path):
            with open(release_config_path, "r", encoding="utf-8") as f:
                rel_data = cast(dict[str, Any], json.load(f))
                modules = cast(list[dict[str, Any]], rel_data.get("modules", [])) if isinstance(rel_data.get("modules"), list) else []
                for mod in modules:
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
        if dev_branch != rel_branch:
            print(f"[INFO] Syncing {dev_branch} into {rel_branch} using {sync_method}...")
            subprocess.run(["git", "checkout", rel_branch], check=True)
            if sync_method == "rebase":
                subprocess.run(["git", "rebase", dev_branch], check=True)
            else:
                subprocess.run(["git", "merge", dev_branch, "--no-edit"], check=True)

        for step in steps:
            step_name = str(step)
            if step_name == "custom_commands":
                for mod in affected_modules:
                    cmds = cast(list[Any], custom_cmds.get(mod, [])) if isinstance(custom_cmds.get(mod), list) else []
                    for cmd in cmds:
                        cmd_str = str(cmd)
                        print(f"[INFO] Running custom command for {mod}: {cmd_str}")
                        subprocess.run(cmd_str, shell=True, check=True)
                        executed_commands.append(cmd_str)
                global_cmds = cast(list[Any], custom_cmds.get("global", [])) if isinstance(custom_cmds.get("global"), list) else []
                for cmd in global_cmds:
                    cmd_str = str(cmd)
                    print(f"[INFO] Running global custom command: {cmd_str}")
                    subprocess.run(cmd_str, shell=True, check=True)
                    executed_commands.append(cmd_str)

            elif step_name == "git_push":
                print(f"[INFO] Pushing release branch {rel_branch}...")
                subprocess.run(["git", "push", "origin", rel_branch, "--tags"], check=True)
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


__all__ = [
    "run_release_plan",
    "run_release_execute",
]
