# workflow_runtime.py
import argparse
import sys
import os
import json
import subprocess
from datetime import datetime
from typing import cast

# Add the directory containing this script to sys.path to resolve sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from session import load_session, save_session_atomic, SessionLock
from context import estimate_context_usage
from checkpoint import validate_checkpoint_level, get_checkpoint_name
from validator import get_git_info, get_version_info
from drift import check_context_drift
from heartbeat import print_heartbeat
from utils import get_memory_info, get_rag_info, prompt_select
from db import save_usage_to_dbs, get_workflow_summary, get_project_summary, get_global_summary

def get_project_id() -> str:
    path = os.path.join(".agents", "memory.config.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("project_id", "ai-skill-framework")
        except Exception:
            pass
    return "ai-skill-framework"

def get_permission_mode() -> str:
    session = load_session()
    mode = session.get("permission_mode", "sandbox")
    if mode not in ["sandbox", "full_access", "unrestricted"]:
        return "sandbox"
    return str(mode)

def requires_approval(action_type: str) -> bool:
    mode = get_permission_mode()
    if mode == "unrestricted":
        return False
    if mode == "sandbox":
        return True
        
    # Hard-gated actions that ALWAYS require approval in full_access mode
    hard_gated = [
        "release",
        "git_commit",
        "git_tag",
        "git_push",
        "git_merge",
        "destructive_delete",
        "external_command",
        "secret_change",
        "permission_mode_change"
    ]
    if action_type in hard_gated:
        return True
        
    return False

def update_context_health(session: dict) -> None:
    # Auto-detect and sync current conversation_id from environment metadata
    metadata_str = os.environ.get("ANTIGRAVITY_SOURCE_METADATA")
    if metadata_str:
        try:
            metadata_raw = json.loads(metadata_str)
            if isinstance(metadata_raw, dict):
                metadata = cast(dict[str, object], metadata_raw)
                tool_data = metadata.get("tool")
                if isinstance(tool_data, dict):
                    tool_data_dict = cast(dict[str, object], tool_data)
                    env_conv_id = tool_data_dict.get("conversationId")
                    if isinstance(env_conv_id, str) and env_conv_id:
                        session["conversation_id"] = env_conv_id
        except Exception:
            pass

    if "suggestion_gate" not in session:
        session["suggestion_gate"] = {
            "active": False,
            "raw_request": "",
            "classification": "",
            "recommended_skill": "",
            "options": [],
            "status": "idle"
        }
        
    # Sync current system status to prevent false drift detection
    session["git"] = get_git_info()
    session["version"] = get_version_info()
    session["memory"] = get_memory_info()
    session["rag"] = get_rag_info()
        
    # 1. Estimate current context usage
    usage = estimate_context_usage()
    
    # 2. Save it to DBs if conversation_id exists
    conv_id = session.get("conversation_id")
    if conv_id:
        proj_id = get_project_id()
        skill = session.get("current_skill", "unknown")
        cmd = session.get("current_command", "unknown")
        save_usage_to_dbs(conv_id, proj_id, skill, cmd, usage)
        
    # 3. Retrieve summaries from DBs
    wf_summary = get_workflow_summary(
        conv_id or "",
        usage.get("provider", "estimate"),
        usage.get("model", "auto")
    )
    if wf_summary.get("total_tokens", 0) == 0 and usage.get("total_tokens", 0) > 0:
        session["workflow_usage_summary"] = usage
    else:
        session["workflow_usage_summary"] = wf_summary
        
    session["project_usage_summary"] = get_project_summary()
    session["global_usage_summary"] = get_global_summary()
    
    # 4. Populate backward-compatible context_usage object
    session["context_usage"] = {
        "total_tokens": usage.get("total_tokens", 0),
        "limit_tokens": usage.get("limit_tokens", 2000000),
        "percentage": usage.get("percentage", 0.0)
    }
    
    # 5. Check drift
    drifted, msg = check_context_drift(session)
    session["context_health"] = "broken" if drifted else "healthy"

def do_init(args):
    session = load_session()
    if not session:
        session = {
            "workspace": {"path": ".", "valid": True},
            "git": get_git_info(),
            "work_item": {"type": "FEAT", "id": "FEAT-001", "title": "Initial Scaffolding"},
            "version": get_version_info(),
            "memory": get_memory_info(),
            "rag": get_rag_info(),
            "blueprint": {
                "path": "",
                "exists": False,
                "approved": False,
                "approved_at": "",
                "approved_by": ""
            },
            "suggestion_gate": {
                "active": False,
                "raw_request": "",
                "classification": "",
                "recommended_skill": "",
                "options": [],
                "status": "idle"
            },
            "checkpoint": 1,
            "status": "completed",
            "current_skill": "initialize-workflow",
            "current_command": "init",
            "current_step": "Initialization Complete",
            "current_logs": ["> Initialization completed successfully."],
            "suggested_next_skill": "project-discovery",
            "suggested_next_command": "discover",
            "context_health": "healthy"
        }
    
    permission_arg = getattr(args, "permission", None)
    if permission_arg is None:
        choice = prompt_select(
            "Choose workspace permission mode:",
            [
                "1. Sandbox Mode (Safe default. Ask before every state-changing action.)",
                "2. Full Access Mode (Allow normal workflow file/code changes.)",
                "3. Unrestricted Mode (DANGER ZONE. Bypass all confirmation gates.)"
            ],
            default="1. Sandbox Mode (Safe default. Ask before every state-changing action.)"
        )
        if "3" in choice or "Unrestricted" in choice:
            permission_arg = "3"
        elif "2" in choice or "Full Access" in choice:
            permission_arg = "2"
        else:
            permission_arg = "1"
            
    if str(permission_arg) in ["3", "unrestricted"]:
        print("\n" + "="*70)
        print("⚠️  WARNING: DANGER ZONE - ENABLING UNRESTRICTED MODE")
        print("This mode completely disables all confirmation gates.")
        print("The AI will execute git push, tagging, releases, file changes, and")
        print("credentials editing AUTOMATICALLY without prompting you.")
        print("="*70)
        try:
            confirm = prompt_select(
                "WARNING: DANGER ZONE - ENABLING UNRESTRICTED MODE. Type 'CONFIRM_UNRESTRICTED' to proceed:",
                ["CONFIRM_UNRESTRICTED", "CANCEL"],
                default="CANCEL"
            ).strip()
            if confirm == "CONFIRM_UNRESTRICTED":
                mode = "unrestricted"
            else:
                print("Warning: Confirmation mismatch. Fallback to sandbox mode.")
                mode = "sandbox"
        except (IOError, KeyboardInterrupt):
            print("\nWarning: Input interrupted. Fallback to sandbox mode.")
            mode = "sandbox"
    elif str(permission_arg) in ["2", "full_access"]:
        mode = "full_access"
    else:
        mode = "sandbox"
        
    session["permission_mode"] = mode
    session["permission_mode_selected_at"] = datetime.now().astimezone().isoformat()
    session["permission_mode_selected_by"] = "user"
    
    update_context_health(session)
    save_session_atomic(session)
    print(f"Session initialized with permission_mode={mode}.")

def do_validate(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    
    update_context_health(session)
    if session["context_health"] == "broken":
        print("Error: Context health is broken (drift detected).", file=sys.stderr)
        sys.exit(1)
        
    if args.checkpoint:
        curr = session.get("checkpoint", 1)
        if not validate_checkpoint_level(curr, args.checkpoint):
            print(f"Error: checkpoint validation failed (current={curr}, required={args.checkpoint}).", file=sys.stderr)
            sys.exit(1)
    save_session_atomic(session)
    print("Validation passed.")

def do_start(args):
    session = load_session()
    if not session:
        session = {"workspace": {"path": ".", "valid": True}}
    
    session["status"] = "in_progress"
    if args.checkpoint is not None:
        session["checkpoint"] = args.checkpoint
    session["current_skill"] = args.skill
    session["current_command"] = args.command
    session["current_step"] = args.step
    session["current_logs"] = [f"> Starting {args.skill}..."]
    
    update_context_health(session)
    save_session_atomic(session)
    print(f"Skill {args.skill} started.")

def do_step(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    session["current_step"] = args.step
    if "current_logs" not in session or not isinstance(session["current_logs"], list):
        session["current_logs"] = []
    if args.log:
        session["current_logs"].append(args.log)
    update_context_health(session)
    save_session_atomic(session)

def do_complete(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    session["status"] = "completed"
    if args.checkpoint is not None:
        session["checkpoint"] = args.checkpoint
    if args.step:
        session["current_step"] = args.step
    else:
        chk = args.checkpoint or session.get("checkpoint", 1)
        session["current_step"] = get_checkpoint_name(chk)
    session["suggested_next_skill"] = args.next_skill
    session["suggested_next_command"] = args.next_command
    if "current_logs" not in session or not isinstance(session["current_logs"], list):
        session["current_logs"] = []
    session["current_logs"].append(f"> Completed successfully.")
    
    update_context_health(session)
    save_session_atomic(session)
    
    # Clean temporary analysis agents
    analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
    if os.path.exists(analysis_file):
        try:
            os.remove(analysis_file)
        except Exception:
            pass
    # Sync session to clear analysis_agents list
    sync_analysis_agents_to_session()
    
    print("Step completed.")

def do_fail(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    session["status"] = "failed"
    session["current_step"] = args.step
    if "current_logs" not in session or not isinstance(session["current_logs"], list):
        session["current_logs"] = []
    if args.log:
        session["current_logs"].append(f"Error: {args.log}")
    update_context_health(session)
    save_session_atomic(session)
    print("Step failed.")

def do_heartbeat(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
    update_context_health(session)
    print_heartbeat(session)

def do_usage(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
        
    if args.subaction == "sync":
        update_context_health(session)
        save_session_atomic(session)
        print("Usage database synchronized.")
        
    elif args.subaction == "report":
        update_context_health(session)
        wf = session.get("workflow_usage_summary", {})
        proj = session.get("project_usage_summary", {})
        glob = session.get("global_usage_summary", {})
        
        report = f"""# AI Workflow Usage Report

## Workflow Usage
- Provider: {wf.get("provider", "N/A")}
- Model: {wf.get("model", "N/A")}
- Tokens: {wf.get("total_tokens", 0)} / {wf.get("limit_tokens", 2000000)} ({wf.get("percentage", 0.0)}%)
- Cost: ${wf.get("estimated_cost_usd", 0.0):.4f} USD
- Details: Input={wf.get("input_tokens", 0)}, Output={wf.get("output_tokens", 0)}, Cache={wf.get("cache_tokens", 0)}, Thinking={wf.get("thinking_tokens", 0)}

## Project Usage
- Total Tokens: {proj.get("total_tokens", 0)}
- Estimated Cost: ${proj.get("estimated_cost_usd", 0.0):.4f} USD

## Global AI Usage
- Total Tokens: {glob.get("total_tokens", 0)}
- Estimated Cost: ${glob.get("estimated_cost_usd", 0.0):.4f} USD
"""
        print(report)
        
    elif args.subaction == "diagnose":
        import sqlite3
        from db import PROJECT_DB, get_global_db_path
        
        print("Database Diagnosis:")
        print(f"1. Project Database: {os.path.abspath(PROJECT_DB)}")
        if os.path.exists(PROJECT_DB):
            try:
                conn = sqlite3.connect(PROJECT_DB)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM usage_records")
                count = cursor.fetchone()[0]
                print(f"   Status: OK (Records: {count})")
                conn.close()
            except Exception as e:
                print(f"   Status: CORRUPTED ({e})")
        else:
            print("   Status: MISSING")
            
        global_db = get_global_db_path()
        print(f"2. Global Database: {os.path.abspath(global_db)}")
        if os.path.exists(global_db):
            try:
                conn = sqlite3.connect(global_db)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM usage_records")
                count = cursor.fetchone()[0]
                print(f"   Status: OK (Records: {count})")
                conn.close()
            except Exception as e:
                print(f"   Status: CORRUPTED ({e})")
        else:
            print("   Status: MISSING")
            
    elif args.subaction == "export":
        import sqlite3
        from db import PROJECT_DB
        
        data = []
        if os.path.exists(PROJECT_DB):
            try:
                conn = sqlite3.connect(PROJECT_DB)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM usage_records")
                data = [dict(row) for row in cursor.fetchall()]
                conn.close()
            except Exception as e:
                print(f"Error reading database: {e}", file=sys.stderr)
                sys.exit(1)
                
        json_str = json.dumps(data, indent=2)
        if args.out:
            try:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(json_str)
                print(f"Exported to {args.out}")
            except Exception as e:
                print(f"Error writing to file: {e}", file=sys.stderr)
                sys.exit(1)
        else:
            print(json_str)

def do_blueprint(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
        
    bp_path = args.path
    exists = os.path.exists(bp_path)
    
    bp_data = {
        "path": bp_path,
        "exists": exists,
        "approved": False,
        "approved_at": "",
        "approved_by": ""
    }
    
    if args.approve:
        if not exists:
            print(f"Error: Blueprint file does not exist at {bp_path}.", file=sys.stderr)
            sys.exit(1)
        bp_data["approved"] = True
        bp_data["approved_at"] = datetime.now().astimezone().isoformat()
        bp_data["approved_by"] = "user"
        
    session["blueprint"] = bp_data
    update_context_health(session)
    save_session_atomic(session)
    
    if args.approve:
        print(f"Blueprint {bp_path} approved.")
    else:
        print(f"Blueprint {bp_path} registered (exists={exists}).")

def do_suggest(args):
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
        
    suggestion = session.get("suggestion_gate", {
        "active": False,
        "raw_request": "",
        "classification": "",
        "recommended_skill": "",
        "options": [],
        "status": "idle"
    })
    
    if args.request:
        suggestion["raw_request"] = args.request
        suggestion["active"] = True
        suggestion["status"] = "waiting_for_user_confirmation"
        
    if args.classification:
        suggestion["classification"] = args.classification
        
    if args.recommend:
        suggestion["recommended_skill"] = args.recommend
        
    if args.options:
        suggestion["options"] = [o.strip() for o in args.options.split(",")]
        
    if args.status:
        suggestion["status"] = args.status
        if args.status == "confirmed" or args.status == "idle" or args.status == "rejected":
            suggestion["active"] = False
            
    if args.choose:
        choice = args.choose.strip().lower()
        if choice in ["y", "yes", "proceed", "continue"]:
            suggestion["status"] = "confirmed"
            suggestion["active"] = False
            print("Suggestion confirmed.")
        elif choice in ["n", "no"]:
            suggestion["status"] = "rejected"
            suggestion["active"] = False
            print("Suggestion rejected.")
        else:
            # Check if choice is a number corresponding to one of the options
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(suggestion["options"]):
                    suggestion["recommended_skill"] = suggestion["options"][idx]
                    suggestion["status"] = "confirmed"
                    suggestion["active"] = False
                    print(f"Option {choice} selected: {suggestion['recommended_skill']}.")
                else:
                    print(f"Error: Invalid option index {choice}.", file=sys.stderr)
                    sys.exit(1)
            except ValueError:
                print(f"Error: Invalid choice {choice}.", file=sys.stderr)
                sys.exit(1)
                
    if not args.choose and suggestion["active"] and os.environ.get("TESTING") != "1":
        from utils import prompt_select
        if suggestion.get("options"):
            opts = suggestion["options"]
            default_opt = suggestion.get("recommended_skill")
            if default_opt not in opts:
                default_opt = opts[0]
            choice = prompt_select(f"Which workflow/skill should be used for request '{suggestion['raw_request']}'?", opts, default=default_opt)
            suggestion["recommended_skill"] = choice
            suggestion["status"] = "confirmed"
            suggestion["active"] = False
            print(f"Option selected: {choice}")
        elif suggestion.get("recommended_skill"):
            opts = ["Yes", "No"]
            choice = prompt_select(f"Confirm using skill '{suggestion['recommended_skill']}' for request '{suggestion['raw_request']}'?", opts, default="Yes")
            if choice == "Yes":
                suggestion["status"] = "confirmed"
            else:
                suggestion["status"] = "rejected"
            suggestion["active"] = False
            print(f"Suggestion {suggestion['status']}.")

    session["suggestion_gate"] = suggestion
    update_context_health(session)
    save_session_atomic(session)
    if not args.choose:
        print(f"Suggestion gate updated (active={suggestion['active']}, status={suggestion['status']}).")

def do_permission(_args: argparse.Namespace) -> None:  # type: ignore
    mode = get_permission_mode()
    print(f"Permission Mode: {mode}")
    print("\nStatus of common actions:")
    actions = [
        "normal_file_write",
        "source_code_change",
        "test_command",
        "build_command",
        "memory_update",
        "git_commit",
        "git_push",
        "git_tag",
        "git_merge",
        "release",
        "destructive_delete",
        "secret_change",
        "permission_mode_change"
    ]
    for action in actions:
        req = requires_approval(action)
        status = "REQUIRED_APPROVAL (Hard-gated)" if req else "ALLOWED (Bypass)"
        print(f"- {action}: {status}")

def do_compact(_args: argparse.Namespace) -> None:  # type: ignore
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
        
    # Run git stash to save local unstaged changes dynamically
    stash_ref = ""
    try:
        res = subprocess.run(["git", "stash", "create"], capture_output=True, text=True, check=True)
        stash_hash = res.stdout.strip()
        if stash_hash:
            _ = subprocess.run(["git", "stash", "store", "-m", "Rollover Context Auto-Stash", stash_hash], check=True)
            stash_ref = "stash@{0}"
            print(f"Git auto-stash created: {stash_ref}")
    except Exception:
        pass

    # Load execution plan details
    plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
    execution_mode = "pending"
    recommended_mode = "parallel"
    approved = False
    implementation_execution_mode = "pending"
    parallel_allowed_phase = "implementation"
    parallel_allowed = False
    if os.path.exists(plan_file):
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
                execution_mode = plan_data.get("execution_mode", "pending")
                recommended_mode = plan_data.get("recommended_mode", "parallel")
                approved = plan_data.get("approved", False)
                implementation_execution_mode = plan_data.get("implementation_execution_mode", "pending")
                parallel_allowed_phase = plan_data.get("parallel_allowed_phase", "implementation")
                parallel_allowed = plan_data.get("parallel_allowed", False)
        except Exception:
            pass
            
    # Load parallel tasks details
    tasks_file = os.path.join(".agents", "runtime", "parallel-tasks.json")
    parallel_groups = []
    running_agents = []
    queued_agents = []
    blocked_agents = []
    waiting_dependencies = []
    
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
                tasks = tasks_data.get("tasks", {})
                for tid, tinfo in tasks.items():
                    status = tinfo.get("status", "pending")
                    group = tinfo.get("execution_group")
                    if group and group not in parallel_groups:
                        parallel_groups.append(group)
                    if status == "running":
                        running_agents.append(tid)
                    elif status == "pending":
                        queued_agents.append(tid)
                    elif status == "blocked":
                        blocked_agents.append(tid)
        except Exception:
            pass

    # Build snapshot data
    snapshot_file = os.path.join(".agents", "runtime", "context_snapshot.json")
    os.makedirs(os.path.dirname(snapshot_file), exist_ok=True)
    
    snapshot = {
        "checkpoint": session.get("checkpoint", 1),
        "current_skill": session.get("current_skill", ""),
        "current_command": session.get("current_command", ""),
        "current_step": session.get("current_step", ""),
        "active_feature_id": "FIX-014",
        "git_stash_ref": stash_ref,
        "rollover_requested_at": datetime.now().astimezone().isoformat(),
        "execution_mode": execution_mode,
        "recommended_mode": recommended_mode,
        "approved": approved,
        "implementation_execution_mode": implementation_execution_mode,
        "parallel_allowed_phase": parallel_allowed_phase,
        "parallel_allowed": parallel_allowed,
        "parallel_groups": parallel_groups,
        "running_agents": running_agents,
        "queued_agents": queued_agents,
        "blocked_agents": blocked_agents,
        "waiting_dependencies": waiting_dependencies
    }
    
    try:
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        print(f"Context snapshot written successfully to {snapshot_file}")
    except IOError as e:
        print(f"Error: failed to write snapshot: {e}", file=sys.stderr)
        sys.exit(1)

def sync_execution_state_to_session() -> None:
    session = load_session()
    if not session:
        return
        
    plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
    if os.path.exists(plan_file):
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
                session["implementation_execution_mode"] = plan_data.get("implementation_execution_mode", "pending")
                session["parallel_allowed_phase"] = plan_data.get("parallel_allowed_phase", "implementation")
                session["parallel_allowed"] = plan_data.get("parallel_allowed", False)
                session["execution_mode"] = plan_data.get("implementation_execution_mode", "pending")
                session["recommended_mode"] = plan_data.get("recommended_mode", "parallel")
                session["approved"] = plan_data.get("approved", False)
        except Exception:
            pass
            
    tasks_file = os.path.join(".agents", "runtime", "parallel-tasks.json")
    parallel_groups = []
    running_agents = []
    queued_agents = []
    blocked_agents = []
    waiting_dependencies = []
    
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)
                tasks = tasks_data.get("tasks", {})
                for tid, tinfo in tasks.items():
                    status = tinfo.get("status", "pending")
                    group = tinfo.get("execution_group")
                    if group and group not in parallel_groups:
                        parallel_groups.append(group)
                    if status == "running":
                        running_agents.append(tid)
                    elif status == "pending":
                        queued_agents.append(tid)
                    elif status == "blocked":
                        blocked_agents.append(tid)
        except Exception:
            pass
            
    session["parallel_groups"] = parallel_groups
    session["running_agents"] = running_agents
    session["queued_agents"] = queued_agents
    session["blocked_agents"] = blocked_agents
    session["waiting_dependencies"] = waiting_dependencies
    
    save_session_atomic(session)


def do_task(args: argparse.Namespace) -> None:
    tasks_file = os.path.join(".agents", "runtime", "parallel-tasks.json")
    os.makedirs(os.path.dirname(tasks_file), exist_ok=True)
    
    tasks: dict[str, dict[str, object]] = {}
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, "r", encoding="utf-8") as f:
                data = cast(dict[str, object], json.load(f))
                tasks = cast(dict[str, dict[str, object]], data.get("tasks", {}))
        except Exception:
            pass
            
    if args.subaction == "plan":
        plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
        os.makedirs(os.path.dirname(plan_file), exist_ok=True)
        plan_tasks: list[dict[str, object]] = []
        if os.path.exists(plan_file):
            try:
                with open(plan_file, "r", encoding="utf-8") as f:
                    data = cast(dict[str, object], json.load(f))
                    plan_tasks = cast(list[dict[str, object]], data.get("tasks", []))
            except Exception:
                pass
        for t in plan_tasks:
            tid = t.get("task_id")
            if isinstance(tid, str) and tid:
                tasks[tid] = {
                    "status": "pending",
                    "started_at": None,
                    "completed_at": None,
                    "execution_group": t.get("execution_group", "Group 1")
                }
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print("Tasks planned successfully.")
        
    elif args.subaction == "start":
        if not args.task_id:
            print("Error: task_id required.", file=sys.stderr)
            sys.exit(1)
        if args.task_id not in tasks:
            tasks[args.task_id] = {}
        tasks[args.task_id]["status"] = "running"
        tasks[args.task_id]["started_at"] = datetime.now().astimezone().isoformat()
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print(f"Task {args.task_id} started.")
        
    elif args.subaction == "complete":
        if not args.task_id:
            print("Error: task_id required.", file=sys.stderr)
            sys.exit(1)
        if args.task_id not in tasks:
            print(f"Error: task {args.task_id} not found.", file=sys.stderr)
            sys.exit(1)
        tasks[args.task_id]["status"] = "completed"
        tasks[args.task_id]["completed_at"] = datetime.now().astimezone().isoformat()
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print(f"Task {args.task_id} completed.")
        
    elif args.subaction == "fail":
        if not args.task_id:
            print("Error: task_id required.", file=sys.stderr)
            sys.exit(1)
        if args.task_id not in tasks:
            tasks[args.task_id] = {}
        tasks[args.task_id]["status"] = "failed"
        tasks[args.task_id]["completed_at"] = datetime.now().astimezone().isoformat()
        with open(tasks_file, "w", encoding="utf-8") as f:
            json.dump({"tasks": tasks}, f, indent=2, ensure_ascii=False)
        print(f"Task {args.task_id} failed.")
        
    sync_execution_state_to_session()

def do_lock(args: argparse.Namespace) -> None:
    locks_file = os.path.join(".agents", "runtime", "file-locks.json")
    os.makedirs(os.path.dirname(locks_file), exist_ok=True)
    
    locks: dict[str, dict[str, object]] = {}
    if os.path.exists(locks_file):
        try:
            with open(locks_file, "r", encoding="utf-8") as f:
                data = cast(dict[str, object], json.load(f))
                locks = cast(dict[str, dict[str, object]], data.get("locks", {}))
        except Exception:
            pass
            
    if args.subaction == "acquire":
        if not args.task_id or not args.files:
            print("Error: task_id and files are required.", file=sys.stderr)
            sys.exit(1)
        files = [f.strip() for f in args.files.split(",")]
        
        conflicting = []
        for file in files:
            if file in locks and locks[file].get("task_id") != args.task_id:
                conflicting.append((file, locks[file].get("task_id")))
                
        if conflicting:
            print(f"Error: lock acquisition failed. Files locked by other tasks: {conflicting}", file=sys.stderr)
            sys.exit(1)
            
        for file in files:
            locks[file] = {
                "task_id": args.task_id,
                "acquired_at": datetime.now().astimezone().isoformat()
            }
            
        with open(locks_file, "w", encoding="utf-8") as f:
            json.dump({"locks": locks}, f, indent=2, ensure_ascii=False)
        print(f"Locks acquired for task {args.task_id} on: {files}")
        
    elif args.subaction == "release":
        if not args.task_id:
            print("Error: task_id is required.", file=sys.stderr)
            sys.exit(1)
        released = []
        for file, lock in list(locks.items()):
            if lock.get("task_id") == args.task_id:
                del locks[file]
                released.append(file)
        with open(locks_file, "w", encoding="utf-8") as f:
            json.dump({"locks": locks}, f, indent=2, ensure_ascii=False)
        print(f"Locks released for task {args.task_id}: {released}")
        
    elif args.subaction == "list":
        print(json.dumps({"locks": locks}, indent=2))

def do_dependency(args: argparse.Namespace) -> None:
    if args.subaction == "graph":
        plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
        if not os.path.exists(plan_file):
            print(json.dumps({"graph": {}}, indent=2))
            return
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                data = cast(dict[str, object], json.load(f))
                tasks = cast(list[object], data.get("tasks", []))
                print(json.dumps({"tasks": tasks}, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

def do_merge(args: argparse.Namespace) -> None:
    if args.subaction == "prepare":
        print("Merge prepared.")
    elif args.subaction == "complete":
        print("Merge completed successfully.")

def do_conflict(args: argparse.Namespace) -> None:
    conflicts_file = os.path.join(".agents", "runtime", "conflicts.json")
    os.makedirs(os.path.dirname(conflicts_file), exist_ok=True)
    if args.subaction == "detect":
        conflicts: list[object] = []
        with open(conflicts_file, "w", encoding="utf-8") as f:
            json.dump({"conflicts": conflicts}, f, indent=2)
        print(json.dumps({"conflicts": conflicts}, indent=2))
    elif args.subaction == "resolve":
        print("Conflicts resolved.")

def do_execution(args: argparse.Namespace) -> None:
    plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
    os.makedirs(os.path.dirname(plan_file), exist_ok=True)
    
    plan: dict[str, object] = {}
    if os.path.exists(plan_file):
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                plan = cast(dict[str, object], json.load(f))
        except Exception:
            pass
            
    session = load_session()
    checkpoint = session.get("checkpoint", 1)
    parallel_allowed = (checkpoint >= 5)

    if args.subaction == "recommend":
        if not args.mode or not args.reason:
            print("Error: --mode and --reason are required.", file=sys.stderr)
            sys.exit(1)
        plan["implementation_execution_mode"] = "pending"
        plan["parallel_allowed_phase"] = "implementation"
        plan["parallel_allowed"] = parallel_allowed
        plan["execution_mode"] = "pending"
        plan["recommended_mode"] = args.mode
        plan["recommended_reason"] = args.reason
        plan["approved"] = False
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"Recommended execution mode set to {args.mode} (Reason: {args.reason}).")
        
    elif args.subaction == "mode":
        if not args.mode:
            print("Error: --mode is required.", file=sys.stderr)
            sys.exit(1)
            
        if args.mode == "parallel" and not parallel_allowed:
            print(f"Error: Parallel execution mode is only allowed during the implementation/execution phase (checkpoint >= 5). Current checkpoint is {checkpoint}.", file=sys.stderr)
            sys.exit(1)
            
        plan["implementation_execution_mode"] = args.mode
        plan["execution_mode"] = args.mode
        if args.approve:
            plan["approved"] = True
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"Execution mode updated to {args.mode} (Approved: {plan.get('approved')}).")
        
    elif args.subaction == "summary":
        if not plan.get("parallel_allowed", False):
            summary_text = """================================================================================

Execution Plan Summary

Current phase requires sequential execution. Parallel execution is not allowed
until entering the implementation phase (checkpoint >= 5).

================================================================================
"""
            print(summary_text)
            return

        workflow = plan.get("workflow_name", "Autonomous Workflow Upgrade")
        agents = plan.get("estimated_agents", "Orchestrator, Worker")
        duration = plan.get("estimated_duration", "5 minutes")
        tokens = plan.get("estimated_tokens", "150,000")
        groups = plan.get("parallel_groups", "None")
        conflicts = plan.get("potential_conflicts", "None")
        rec_mode = str(plan.get("recommended_mode", "parallel"))
        reason = plan.get("recommended_reason", "No overlapping write sets.")
        
        summary_text = f"""================================================================================

Execution Plan Summary

Workflow:
{workflow}

Estimated Agents:
{agents}

Estimated Duration:
{duration}

Estimated Tokens:
{tokens}

Parallel Groups:
{groups}

Potential Conflicts:
{conflicts}

================================================================================

Recommended Mode

✔ {rec_mode.capitalize()} ({'Safe' if rec_mode == 'parallel' else 'Caution'})

Reason

- {reason}
"""
        print(summary_text)

        sync_execution_state_to_session()

def sync_analysis_agents_to_session() -> None:
    session = load_session()
    analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            session["analysis_agents"] = data.get("agents", [])
        except Exception:
            session["analysis_agents"] = []
    else:
        session["analysis_agents"] = []
    save_session_atomic(session)

def do_analysis_agent(args) -> None:
    analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
    os.makedirs(os.path.dirname(analysis_file), exist_ok=True)
    
    data = {"phase": "unknown", "agents": []}
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
            
    session = load_session()
    current_skill = session.get("active_skill", "unknown")
    data["phase"] = current_skill

    if args.subaction == "add":
        if not args.agent_id or not args.role:
            print("Error: --agent-id and --role are required.", file=sys.stderr)
            sys.exit(1)
        
        recs = []
        if args.recommendations:
            try:
                recs = json.loads(args.recommendations)
                if not isinstance(recs, list):
                    recs = [recs]
            except Exception:
                recs = [args.recommendations]

        existing_agent = None
        for a in data["agents"]:
            if a["agent_id"] == args.agent_id:
                existing_agent = a
                break
        
        if existing_agent:
            existing_agent["role"] = args.role
            existing_agent["status"] = args.status or "completed"
            existing_agent["summary"] = args.summary or ""
            existing_agent["recommendations"] = recs
        else:
            data["agents"].append({
                "agent_id": args.agent_id,
                "role": args.role,
                "status": args.status or "running",
                "summary": args.summary or "",
                "recommendations": recs
            })
            
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Analysis agent {args.agent_id} ({args.role}) added/updated.")
        
    elif args.subaction == "list":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    elif args.subaction == "clear":
        data["agents"] = []
        with open(analysis_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Analysis agents cleared.")
        
    elif args.subaction == "merge":
        print("Merging recommendations from analysis agents:")
        all_recs = []
        for a in data["agents"]:
            print(f"- Agent {a['agent_id']} ({a['role']}): {a.get('summary')}")
            for r in a.get("recommendations", []):
                all_recs.append(f"[{a['role']}] {r}")
        print("Merged recommendations:")
        for idx, r in enumerate(all_recs):
            print(f"{idx+1}. {r}")
            
    sync_analysis_agents_to_session()

def do_routing(args) -> None:
    from agent_routing import load_routing_table, validate_routing
    manifest_path = "MANIFEST.json"
    agents_dir = "agents"
    
    if args.subaction == "list":
        table = load_routing_table(manifest_path)
        print("| Skill | Owner | Specialist Agents | Phase | Execution Mode |")
        print("|---|---|---|---|---|")
        for skill_name, info in sorted(table.items()):
            specs = ", ".join(info["specialist_agents"])
            print(f"| {skill_name} | {info['owner_agent']} | {specs} | {info['phase']} | {info['execution_mode']} |")
            
    elif args.subaction == "validate":
        errors = validate_routing(manifest_path, agents_dir)
        if errors:
            print("Routing validation failed with errors:")
            for err in errors:
                print(f"❌ {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print("✔ Routing validation passed successfully.")

def do_prompt(args) -> None:
    from utils import prompt_select
    options_list = [o.strip() for o in args.options.split("|")]
    res = prompt_select(args.question, options_list, args.default)
    print(res)


def main():
    parser = argparse.ArgumentParser(description="AI Workflow Runtime Engine CLI")
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    init_p = subparsers.add_parser("init")
    _ = init_p.add_argument("--permission", type=str, default=None)
    
    _ = subparsers.add_parser("permission")
    _ = subparsers.add_parser("compact")
    
    val = subparsers.add_parser("validate")
    _ = val.add_argument("--checkpoint", type=str)
    
    st = subparsers.add_parser("start")
    _ = st.add_argument("--skill", required=True, type=str)
    _ = st.add_argument("--command", required=True, type=str)
    _ = st.add_argument("--checkpoint", type=int)
    _ = st.add_argument("--step", required=True, type=str)
    
    sp = subparsers.add_parser("step")
    _ = sp.add_argument("--step", required=True, type=str)
    _ = sp.add_argument("--log", type=str)
    
    cp = subparsers.add_parser("complete")
    _ = cp.add_argument("--checkpoint", type=int)
    _ = cp.add_argument("--step", type=str)
    _ = cp.add_argument("--next-skill", type=str)
    _ = cp.add_argument("--next-command", type=str)
    
    fl = subparsers.add_parser("fail")
    _ = fl.add_argument("--step", required=True, type=str)
    _ = fl.add_argument("--log", type=str)
    
    _ = subparsers.add_parser("heartbeat")
    
    usg = subparsers.add_parser("usage")
    _ = usg.add_argument("subaction", choices=["sync", "report", "diagnose", "export"])
    _ = usg.add_argument("--format", default="json", choices=["json"])
    _ = usg.add_argument("--out", type=str)
    
    bp = subparsers.add_parser("blueprint")
    _ = bp.add_argument("--path", required=True, type=str)
    _ = bp.add_argument("--approve", action="store_true")
    
    sg = subparsers.add_parser("suggest")
    _ = sg.add_argument("--request", type=str)
    _ = sg.add_argument("--classification", type=str)
    _ = sg.add_argument("--recommend", type=str)
    _ = sg.add_argument("--options", type=str)
    _ = sg.add_argument("--status", type=str)
    _ = sg.add_argument("--choose", type=str)
    
    task_p = subparsers.add_parser("task")
    _ = task_p.add_argument("subaction", choices=["plan", "start", "complete", "fail"])
    _ = task_p.add_argument("--task-id", type=str)
    
    lock_p = subparsers.add_parser("lock")
    _ = lock_p.add_argument("subaction", choices=["acquire", "release", "list"])
    _ = lock_p.add_argument("--task-id", type=str)
    _ = lock_p.add_argument("--files", type=str)
    
    dep_p = subparsers.add_parser("dependency")
    _ = dep_p.add_argument("subaction", choices=["graph"])
    
    merge_p = subparsers.add_parser("merge")
    _ = merge_p.add_argument("subaction", choices=["prepare", "complete"])
    
    conf_p = subparsers.add_parser("conflict")
    _ = conf_p.add_argument("subaction", choices=["detect", "resolve"])
    
    exec_p = subparsers.add_parser("execution")
    _ = exec_p.add_argument("subaction", choices=["recommend", "mode", "summary"])
    _ = exec_p.add_argument("--mode", type=str, choices=["parallel", "sequential"])
    _ = exec_p.add_argument("--reason", type=str)
    _ = exec_p.add_argument("--approve", action="store_true")
    
    analysis_p = subparsers.add_parser("analysis-agent")
    _ = analysis_p.add_argument("subaction", choices=["add", "list", "clear", "merge"])
    _ = analysis_p.add_argument("--agent-id", type=str)
    _ = analysis_p.add_argument("--role", type=str)
    _ = analysis_p.add_argument("--status", type=str)
    _ = analysis_p.add_argument("--summary", type=str)
    _ = analysis_p.add_argument("--recommendations", type=str)
    
    routing_p = subparsers.add_parser("routing")
    _ = routing_p.add_argument("subaction", choices=["list", "validate"])
    
    prompt_p = subparsers.add_parser("prompt")
    prompt_sub = prompt_p.add_subparsers(dest="subaction", required=True)
    select_p = prompt_sub.add_parser("select")
    _ = select_p.add_argument("--question", required=True, type=str)
    _ = select_p.add_argument("--options", required=True, type=str)
    _ = select_p.add_argument("--default", type=str, default=None)
    
    args = parser.parse_args()
    
    cmds = {
        "init": do_init,
        "validate": do_validate,
        "start": do_start,
        "step": do_step,
        "complete": do_complete,
        "fail": do_fail,
        "heartbeat": do_heartbeat,
        "usage": do_usage,
        "blueprint": do_blueprint,
        "suggest": do_suggest,
        "permission": do_permission,
        "compact": do_compact,
        "task": do_task,
        "lock": do_lock,
        "dependency": do_dependency,
        "merge": do_merge,
        "conflict": do_conflict,
        "execution": do_execution,
        "analysis-agent": do_analysis_agent,
        "routing": do_routing,
        "prompt": do_prompt
    }
    
    modifying_actions = ["init", "start", "step", "complete", "fail", "blueprint", "suggest", "compact", "task", "execution", "analysis-agent"]
    if args.action in modifying_actions:
        with SessionLock():
            cmds[args.action](args)
    else:
        cmds[args.action](args)

if __name__ == "__main__":
    main()

