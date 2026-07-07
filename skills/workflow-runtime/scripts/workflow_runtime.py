# workflow_runtime.py
import argparse
import sys
import os
import json
import subprocess
from datetime import datetime

# Add the directory containing this script to sys.path to resolve sibling modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from session import load_session, save_session_atomic
from context import estimate_context_usage
from checkpoint import validate_checkpoint_level, get_checkpoint_name
from validator import get_git_info, get_version_info
from drift import check_context_drift
from heartbeat import print_heartbeat
from utils import get_memory_info, get_rag_info
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
    
    permission_arg = getattr(args, "permission", "1")
    if str(permission_arg) in ["3", "unrestricted"]:
        print("\n" + "="*70)
        print("⚠️  WARNING: DANGER ZONE - ENABLING UNRESTRICTED MODE")
        print("This mode completely disables all confirmation gates.")
        print("The AI will execute git push, tagging, releases, file changes, and")
        print("credentials editing AUTOMATICALLY without prompting you.")
        print("="*70)
        try:
            confirm = input("To proceed, type 'CONFIRM_UNRESTRICTED': ").strip()
            if confirm == "CONFIRM_UNRESTRICTED":
                mode = "unrestricted"
            else:
                print("Warning: Confirmation mismatch. Fallback to sandbox mode.")
                mode = "sandbox"
        except (EOFError, KeyboardInterrupt):
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

def do_validate(args: argparse.Namespace) -> None:  # type: ignore
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
            
    # Check context usage for warning gate
    if os.environ.get("SIMULATE_LIMIT") == "1":
        session["context_usage"] = {
            "total_tokens": 1700000,
            "limit_tokens": 2000000,
            "percentage": 85.0
        }
    context_usage = session.get("context_usage", {})
    pct = context_usage.get("percentage", 0.0)
    if pct >= 85.0:
        print("\033[91m⚠️ [SYSTEM WARNING]: Context limit is at {:.1f}% ({}/{} tokens). To prevent slowdowns, please restart the chat session. Run '/workflow reset' to rollover safely.\033[0m".format(
            pct, context_usage.get("total_tokens", 0), context_usage.get("limit_tokens", 0)
        ))
        
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

    # Build snapshot data
    snapshot_file = os.path.join(".agents", "runtime", "context_snapshot.json")
    os.makedirs(os.path.dirname(snapshot_file), exist_ok=True)
    
    snapshot = {
        "checkpoint": session.get("checkpoint", 1),
        "current_skill": session.get("current_skill", ""),
        "current_command": session.get("current_command", ""),
        "current_step": session.get("current_step", ""),
        "active_feature_id": "FEAT-014",
        "git_stash_ref": stash_ref,
        "rollover_requested_at": datetime.now().astimezone().isoformat()
    }
    
    try:
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        print(f"Context snapshot written successfully to {snapshot_file}")
    except IOError as e:
        print(f"Error: failed to write snapshot: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Workflow Runtime Engine CLI")
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    init_p = subparsers.add_parser("init")
    init_p.add_argument("--permission", type=str, default="1")
    
    _perm_p = subparsers.add_parser("permission")
    _compact_p = subparsers.add_parser("compact")
    
    val = subparsers.add_parser("validate")
    val.add_argument("--checkpoint", type=str)
    
    st = subparsers.add_parser("start")
    st.add_argument("--skill", required=True, type=str)
    st.add_argument("--command", required=True, type=str)
    st.add_argument("--checkpoint", type=int)
    st.add_argument("--step", required=True, type=str)
    
    sp = subparsers.add_parser("step")
    sp.add_argument("--step", required=True, type=str)
    sp.add_argument("--log", type=str)
    
    cp = subparsers.add_parser("complete")
    cp.add_argument("--checkpoint", type=int)
    cp.add_argument("--step", type=str)
    cp.add_argument("--next-skill", type=str)
    cp.add_argument("--next-command", type=str)
    
    fl = subparsers.add_parser("fail")
    fl.add_argument("--step", required=True, type=str)
    fl.add_argument("--log", type=str)
    
    subparsers.add_parser("heartbeat")
    
    usg = subparsers.add_parser("usage")
    usg.add_argument("subaction", choices=["sync", "report", "diagnose", "export"])
    usg.add_argument("--format", default="json", choices=["json"])
    usg.add_argument("--out", type=str)
    
    bp = subparsers.add_parser("blueprint")
    bp.add_argument("--path", required=True, type=str)
    bp.add_argument("--approve", action="store_true")
    
    sg = subparsers.add_parser("suggest")
    sg.add_argument("--request", type=str)
    sg.add_argument("--classification", type=str)
    sg.add_argument("--recommend", type=str)
    sg.add_argument("--options", type=str)
    sg.add_argument("--status", type=str)
    sg.add_argument("--choose", type=str)
    
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
        "compact": do_compact
    }
    
    cmds[args.action](args)

if __name__ == "__main__":
    main()
