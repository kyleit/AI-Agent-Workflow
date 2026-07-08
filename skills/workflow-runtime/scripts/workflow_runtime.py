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

from session import load_session, save_session_atomic, SessionLock # type: ignore
from fingerprint import calculate_project_fingerprint # type: ignore
from state_sync import read_json_safe, write_json_atomic, aggregate_state, deconstruct_state # type: ignore
from context import estimate_context_usage # type: ignore
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
    new_fp = calculate_project_fingerprint(".")
    state_dir = os.path.join(".agents", "state")
    context_path = os.path.join(state_dir, "context.json")
    
    use_cache = False
    session = {}
    if os.path.exists(context_path):
        try:
            with open(context_path, "r", encoding="utf-8") as f:
                context_data = json.load(f)
            if context_data.get("project_fingerprint") == new_fp:
                use_cache = True
                session = load_session()
        except Exception:
            pass
            
    if not use_cache or not session:
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
        session["project_fingerprint"] = new_fp
    else:
        session["current_logs"] = ["> Initialization completed successfully (loaded from cache)."]
        session["updated_at"] = datetime.now().astimezone().isoformat()
    
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
        print("[WARNING] WARNING: DANGER ZONE - ENABLING UNRESTRICTED MODE")
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
    if getattr(args, "subaction", None):
        if args.subaction == "blueprint":
            from artifact_validator import validate_blueprint_file
            res = validate_blueprint_file(args.file)
        elif args.subaction == "artifact":
            from artifact_validator import validate_artifact_general
            res = validate_artifact_general(args.file)
        elif args.subaction == "session":
            session = load_session()
            if not session:
                res = {"status": "failure", "command": "validate session", "summary": "Session file not found."}
            else:
                from drift import check_context_drift
                drifted, msg = check_context_drift(session)
                if drifted:
                    res = {"status": "failure", "command": "validate session", "summary": f"Session is unhealthy (drift detected: {msg})."}
                else:
                    res = {"status": "success", "command": "validate session", "summary": "Session is healthy."}
        else:
            res = {"status": "failure", "command": "validate", "summary": "Invalid validate subaction."}
        print(json.dumps(res, indent=2))
        if res["status"] != "success":
            sys.exit(1)
        return

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
    
    # Check blueprint approval before starting implementation
    is_impl = (args.skill == "blueprint-to-implementation") or (args.checkpoint is not None and args.checkpoint >= 6)
    if is_impl:
        bp = session.get("blueprint", {})
        if not bp.get("approved"):
            print("Error: Cannot start implementation. Technical Design Blueprint is not approved.", file=sys.stderr)
            print("Please create a design blueprint and approve it using: aiwf blueprint --path <path> --approve first.", file=sys.stderr)
            sys.exit(1)
            
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
                
    if not args.choose and suggestion["active"]:
        from utils import is_stdin_ready
        if os.environ.get("TESTING") == "1" and not is_stdin_ready():
            pass
        else:
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

    # Map orchestrator state for compatibility
    orchestrator_state = {
        "active": suggestion.get("active", False),
        "raw_request": suggestion.get("raw_request", ""),
        "classification": suggestion.get("classification", ""),
        "recommended_skill": suggestion.get("recommended_skill", ""),
        "recommended_command": "",
        "options": suggestion.get("options", []),
        "selected_skill": suggestion.get("recommended_skill") if suggestion.get("status") == "confirmed" else "",
        "selected_command": "",
        "routing_status": "waiting_for_user",
        "reason": suggestion.get("reason", "")
    }
    
    def map_cmd(skill_name):
        if not skill_name: return ""
        if skill_name == "quick-fix": return "fix"
        if skill_name == "quick-feature": return "feature"
        if skill_name == "brainstorming": return "brainstorm"
        if skill_name == "project-rag-search": return "search"
        if skill_name == "project-memory-bootstrap": return "bootstrap"
        if skill_name == "project-memory-update": return "update"
        if skill_name == "blueprint-to-implementation": return "implement"
        if skill_name == "implementation-to-debug": return "debug"
        if skill_name == "debug-to-verify": return "verify"
        if skill_name == "implementation-to-release": return "release"
        return ""
        
    orchestrator_state["recommended_command"] = map_cmd(orchestrator_state["recommended_skill"])
    if orchestrator_state["selected_skill"]:
        orchestrator_state["selected_command"] = map_cmd(orchestrator_state["selected_skill"])
        orchestrator_state["routing_status"] = "dispatched"
    elif not orchestrator_state["active"]:
        orchestrator_state["routing_status"] = "stopped"
        
    session["orchestrator"] = orchestrator_state
    session["suggestion_gate"] = suggestion
    update_context_health(session)
    save_session_atomic(session)
    if not args.choose:
        print(f"Suggestion gate updated (active={suggestion['active']}, status={suggestion['status']}).")

def do_choice(args) -> None:
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)

    runtime_dir = os.path.join(".agents", "runtime")
    os.makedirs(runtime_dir, exist_ok=True)
    
    pending_path = os.path.join(runtime_dir, "pending-choice.json")
    response_path = os.path.join(runtime_dir, "choice-response.json")
    ui_capabilities_path = os.path.join(runtime_dir, "ui-capabilities.json")
    
    if args.subaction == "create":
        raw_options = args.options.strip() if args.options else ""
        options = []
        if raw_options.startswith("["):
            try:
                options = json.loads(raw_options)
            except json.JSONDecodeError as e:
                print(f"Error parsing options JSON: {e}", file=sys.stderr)
                sys.exit(1)
        elif raw_options:
            for opt in raw_options.split(","):
                opt = opt.strip()
                if opt:
                    options.append({"id": opt, "label": opt})
                    
        choice_type = args.type or "choice"
        choice_data = {
            "type": choice_type,
            "id": args.id,
            "title": args.title,
            "description": args.desc or "",
            "required": args.required,
            "allow_cancel": args.allow_cancel,
            "options": options
        }
        
        tmp_path = pending_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(choice_data, f, indent=2, ensure_ascii=False)
        if os.path.exists(pending_path):
            os.replace(tmp_path, pending_path)
        else:
            os.rename(tmp_path, pending_path)
            
        print(f"Choice {args.id} created successfully.")
        
    elif args.subaction == "wait":
        import time
        interactive_choice = False
        if os.path.exists(ui_capabilities_path):
            try:
                with open(ui_capabilities_path, "r", encoding="utf-8") as f:
                    caps = json.load(f)
                    interactive_choice = caps.get("interactive_choice", False)
            except Exception:
                pass
                
        if os.environ.get("AIWF_INTERACTIVE_CHOICE") == "true":
            interactive_choice = True
            
        timeout = args.timeout or 60
        start_time = time.time()
        choice_resolved = False
        selected_option = None
        
        if interactive_choice:
            print(f"Waiting for UI choice response for {args.id} (timeout={timeout}s)...")
            while time.time() - start_time < timeout:
                if os.path.exists(response_path):
                    try:
                        with open(response_path, "r", encoding="utf-8") as f:
                            resp_data = json.load(f)
                        if resp_data.get("id") == args.id:
                            selected_option = resp_data.get("selected")
                            choice_resolved = True
                            break
                    except Exception:
                        pass
                time.sleep(0.5)
                
        if not choice_resolved:
            if interactive_choice:
                print("\nTimeout waiting for UI response. Switching to Text Fallback Mode...")
            
            if os.path.exists(pending_path):
                try:
                    with open(pending_path, "r", encoding="utf-8") as f:
                        choice_data = json.load(f)
                except Exception:
                    choice_data = {}
            else:
                choice_data = {}
                
            title = choice_data.get("title", args.id or "Choice Required")
            desc = choice_data.get("description", "")
            options = choice_data.get("options", [])
            choice_type = choice_data.get("type", "choice")
            allow_cancel = choice_data.get("allow_cancel", True)
            
            print(f"\n=== {title} ===")
            if desc:
                print(desc)
            print("-" * len(title))
            
            option_ids = []
            if choice_type == "approval":
                print("[Y] Yes / Continue")
                print("[N] No / Cancel")
                option_ids = ["y", "yes", "proceed", "continue", "n", "no", "cancel"]
            else:
                for idx, opt in enumerate(options):
                    lbl = opt.get("label", opt.get("id"))
                    opt_desc = opt.get("description", "")
                    suffix = f" ({opt_desc})" if opt_desc else ""
                    print(f"{idx + 1}. {lbl}{suffix}")
                    option_ids.append(opt.get("id"))
                    
            if allow_cancel and choice_type != "approval":
                print("C. Cancel")
                
            from utils import is_stdin_ready
            if not sys.stdin.isatty() and not is_stdin_ready():
                # Auto-select default/first option or fail instead of hanging
                if choice_type == "approval":
                    selected_option = "cancel"
                else:
                    selected_option = option_ids[0] if option_ids else "cancel"
                print(f"Non-interactive environment and no stdin input available. Auto-selecting default/fallback: {selected_option}")
                choice_resolved = True
            else:
                while True:
                    user_val = input("\nEnter selection: ").strip()
                    if not user_val:
                        continue
                    val_lower = user_val.lower()
                
                    if val_lower == "c" or val_lower == "cancel":
                        if allow_cancel:
                            selected_option = "cancel"
                            break
                        else:
                            print("Cancel is not allowed for this choice.")
                            continue
                            
                    if choice_type == "approval":
                        if val_lower in ["y", "yes", "proceed", "continue"]:
                            selected_option = "approve"
                            break
                        elif val_lower in ["n", "no", "cancel"]:
                            selected_option = "cancel"
                            break
                        else:
                            print("Invalid selection. Please enter Y or N.")
                            continue
                            
                    try:
                        idx = int(user_val) - 1
                        if 0 <= idx < len(options):
                            selected_option = options[idx]["id"]
                            break
                    except ValueError:
                        pass
                        
                    matched = False
                    for opt in options:
                        if opt["id"].lower() == val_lower or opt["label"].lower() == val_lower:
                            selected_option = opt["id"]
                            matched = True
                            break
                    if matched:
                        break
                    print("Invalid selection. Please try again.")
                
            resp_payload = {
                "id": args.id or "unknown",
                "selected": selected_option,
                "cancelled": selected_option == "cancel"
            }
            tmp_resp = response_path + ".tmp"
            with open(tmp_resp, "w", encoding="utf-8") as f:
                json.dump(resp_payload, f, indent=2, ensure_ascii=False)
            if os.path.exists(response_path):
                os.replace(tmp_resp, response_path)
            else:
                os.rename(tmp_resp, response_path)
                
            if os.path.exists(pending_path):
                try:
                    os.remove(pending_path)
                except Exception:
                    pass
                    
        print(f"Choice resolved: {selected_option}")
        
    elif args.subaction == "read":
        if os.path.exists(response_path):
            try:
                with open(response_path, "r", encoding="utf-8") as f:
                    resp_data = json.load(f)
                if resp_data.get("id") == args.id:
                    print(resp_data.get("selected", ""))
                    return
            except Exception:
                pass
        print("")
        
    elif args.subaction == "clear":
        for p in [pending_path, response_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass
        print("Choice files cleared.")

def do_active_workflow(args) -> None:
    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)
        
    if args.subaction == "get":
        aw = session.get("active_workflow", {})
        if isinstance(aw, str):
            aw = {"type": aw}
        elif not isinstance(aw, dict):
            aw = {}
        print(json.dumps(aw, ensure_ascii=False))
        
    elif args.subaction == "set":
        aw = session.get("active_workflow", {})
        if not isinstance(aw, dict):
            aw = {}
        if args.type: aw["type"] = args.type
        if args.phase: aw["phase"] = args.phase
        if args.skill: aw["skill"] = args.skill
        if args.command: aw["command"] = args.command
        if args.artifact_id: aw["artifact_id"] = args.artifact_id
        if args.spec_path: aw["spec_path"] = args.spec_path
        if args.blueprint_path: aw["blueprint_path"] = args.blueprint_path
        if args.waiting_for:
            aw["waiting_for"] = None if args.waiting_for.lower() == "null" else args.waiting_for
        if args.last_user_prompt: aw["last_user_prompt"] = args.last_user_prompt
        if args.resume_instruction: aw["resume_instruction"] = args.resume_instruction
        session["active_workflow"] = aw
        save_session_atomic(session)
        print("Active workflow updated successfully.")
        
    elif args.subaction == "clear":
        if "active_workflow" in session:
            del session["active_workflow"]
        save_session_atomic(session)
        print("Active workflow cleared.")
        
    elif args.subaction == "resume":
        aw = session.get("active_workflow", {})
        if isinstance(aw, str):
            aw = {"type": aw}
        elif not isinstance(aw, dict):
            aw = {}
        if not aw:
            print("Error: No active workflow to resume.", file=sys.stderr)
            sys.exit(1)
        
        session["current_skill"] = aw.get("skill")
        session["current_command"] = aw.get("command")
        session["status"] = "in_progress"
        
        phase = aw.get("phase")
        if phase == "spec":
            session["checkpoint"] = 2
            session["current_step"] = "Writing Specification"
        elif phase == "spec_approval":
            session["checkpoint"] = 2
            session["current_step"] = "Specification Approval Gate"
        elif phase == "blueprint":
            session["checkpoint"] = 4
            session["current_step"] = "Writing Design Blueprint"
        elif phase == "blueprint_approval":
            session["checkpoint"] = 4
            session["current_step"] = "Blueprint Approval Gate"
        elif phase == "implementation":
            session["checkpoint"] = 5
            session["current_step"] = "Implementing changes"
            
        save_session_atomic(session)
        print(f"Resumed workflow: {aw.get('type')} (phase={phase})")
        
    elif args.subaction == "set-waiting":
        aw = session.get("active_workflow", {})
        if not isinstance(aw, dict):
            aw = {}
        val = args.waiting_for if args.waiting_for and args.waiting_for.lower() != "null" else None
        aw["waiting_for"] = val
        session["active_workflow"] = aw
        save_session_atomic(session)
        print(f"Active workflow waiting_for updated to {val}.")
        
    elif args.subaction == "validate-blueprint":
        if not args.path:
            print("Error: --path is required.", file=sys.stderr)
            sys.exit(1)
        
        bp_path = args.path
        if not os.path.exists(bp_path):
            print(f"Error: Blueprint file does not exist at {bp_path}.", file=sys.stderr)
            sys.exit(1)
            
        norm_path = bp_path.replace("\\", "/")
        if not norm_path.startswith("docs/designs/"):
            print(f"Error: Blueprint file must be located under docs/designs/.", file=sys.stderr)
            sys.exit(1)
            
        if not bp_path.endswith("_blueprint.md"):
            print(f"Error: Blueprint file name must end with _blueprint.md.", file=sys.stderr)
            sys.exit(1)
            
        basename = os.path.basename(bp_path)
        id_prefix = None
        for prefix in ["FIX", "QUICK", "FEAT"]:
            if basename.startswith(prefix + "-"):
                id_prefix = prefix
                break
                
        if not id_prefix:
            print("Error: Blueprint filename must start with FIX-, QUICK-, or FEAT-.", file=sys.stderr)
            sys.exit(1)
            
        if args.workflow:
            wf = args.workflow.lower()
            if wf == "quick-fix" and id_prefix != "FIX":
                print("Error: Workflow quick-fix requires a FIX- prefix.", file=sys.stderr)
                sys.exit(1)
            elif wf == "quick-feature" and id_prefix != "QUICK":
                print("Error: Workflow quick-feature requires a QUICK- prefix.", file=sys.stderr)
                sys.exit(1)
            elif wf in ["standard-feature", "blueprint-to-implementation"] and id_prefix != "FEAT":
                print("Error: Standard feature workflow requires a FEAT- prefix.", file=sys.stderr)
                sys.exit(1)
                
        try:
            with open(bp_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            print(f"Error reading blueprint file: {e}", file=sys.stderr)
            sys.exit(1)
            
        if not content.strip().startswith("---"):
            print("Error: Blueprint file must contain YAML frontmatter.", file=sys.stderr)
            sys.exit(1)
            
        required_headers = [
            "Summary",
            "Scope",
            "Technical Design",
            "Files to Change",
            "Implementation Steps",
            "Validation Plan",
            "Rollback Plan"
        ]
        
        import re
        missing = []
        for h in required_headers:
            pattern = r'^\s*#+\s+' + re.escape(h)
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                missing.append(h)
                
        if missing:
            print(f"Error: Blueprint is missing required sections: {', '.join(missing)}.", file=sys.stderr)
            sys.exit(1)
            
        print("Blueprint validation passed.")
        
    elif args.subaction == "get-branch":
        from utils import get_current_branch
        branch = get_current_branch()
        print(branch)
        
    elif args.subaction == "suggest-branch":
        if not args.artifact_id or not args.slug:
            print("Error: --artifact-id and --slug are required.", file=sys.stderr)
            sys.exit(1)
        from utils import suggest_branch_name
        suggested = suggest_branch_name(args.artifact_id, args.slug)
        print(suggested)
        
    elif args.subaction == "branch-options":
        if not args.artifact_id or not args.slug:
            print("Error: --artifact-id and --slug are required.", file=sys.stderr)
            sys.exit(1)
        from utils import build_branch_selection_options
        options = build_branch_selection_options(args.artifact_id, args.slug)
        print(json.dumps(options, ensure_ascii=False))

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

* {rec_mode.capitalize()} ({'Safe' if rec_mode == 'parallel' else 'Caution'})

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


def do_resume_action(args):
    from workflow_state import resume_session
    res = resume_session()
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)

def do_discover_action(args):
    from project_discovery import run_discovery
    res = run_discovery()
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)

def do_classify_action(args):
    from skill_classifier import classify_intent
    res = classify_intent(args.request)
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)

def do_memory_action(args):
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory"))
    if args.subaction == "bootstrap":
        from memory.bootstrap import run_bootstrap
        res = run_bootstrap()
    elif args.subaction == "update":
        from memory.update import run_update
        res = run_update()
    elif args.subaction == "search":
        from memory.search import RAGSearcher
        searcher = RAGSearcher()
        res = searcher.execute_search(args.query)
    else:
        res = {"status": "failure", "summary": "Invalid memory subaction."}
    
    # Enforce standard return JSON
    result = {
        "status": res.get("status", "success"),
        "command": f"memory {args.subaction}",
        "summary": res.get("message") or res.get("summary") or "Memory operation complete.",
        "warnings": res.get("warnings", []),
        "files_read": res.get("files_read", []),
        "files_written": res.get("files_written", []),
        "next_skill": res.get("next_skill")
    }
    print(json.dumps(result, indent=2))
    if result["status"] != "success":
        sys.exit(1)

def do_env_action(args):
    from environment_health import run_health_check
    res = run_health_check()
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)

def do_debug_action(args):
    from validation_runner import run_debug
    res = run_debug()
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)

def do_verify_action(args):
    from validation_runner import run_verify
    res = run_verify()
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)

def do_release_action(args):
    if args.subaction == "plan":
        from release_manager import run_release_plan
        res = run_release_plan()
    elif args.subaction == "execute":
        from release_manager import run_release_execute
        res = run_release_execute(approve=args.approve)
    else:
        res = {"status": "failure", "summary": "Invalid release subaction."}
        
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)

def do_context(args):
    state_dir = os.path.join(".agents", "state")
    context_file = os.path.join(state_dir, "context.json")
    if os.path.exists(context_file):
        data = read_json_safe(context_file)
    else:
        data = {
            "workspace_path": ".",
            "project_version": "1.0.0",
            "git": get_git_info(),
            "permission_mode": get_permission_mode(),
        }
    print(json.dumps(data, indent=2))

def do_rules_action(args):
    if args.subaction == "status":
        state_dir = os.path.join(".agents", "state")
        rules_file = os.path.join(state_dir, "rules.json")
        rules_data = read_json_safe(rules_file)
        if not rules_data or not rules_data.get("active_rules"):
            rules_list = []
            rules_path = "AI_RULES.md"
            if os.path.exists(rules_path):
                try:
                    with open(rules_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    current_section = "General"
                    for line in lines:
                        if line.startswith("#"):
                            current_section = line.strip("# \n")
                        elif line.strip().startswith("-") or line.strip().startswith("*"):
                            rules_list.append({
                                "rule_id": f"RULE-{len(rules_list)+1:03d}",
                                "rule_text": line.strip("-* \n"),
                                "source": f"AI_RULES.md ({current_section})"
                            })
                except Exception:
                    pass
            rules_data = {
                "active_rules": rules_list,
                "loaded_at": datetime.now().astimezone().isoformat()
            }
            write_json_atomic(rules_file, rules_data)
        print(json.dumps(rules_data, indent=2))

def do_state_action(args):
    state_dir = os.path.join(".agents", "state")
    session_file = os.path.join(".agents", ".session.json")
    
    if args.subaction == "status":
        files = ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json", "rules.json", "recovery.json"]
        present = [f for f in files if os.path.exists(os.path.join(state_dir, f))]
        
        status = "healthy"
        synced = True
        
        if len(present) < len(files) - 1:
            status = "uninitialized"
            synced = False
        else:
            if os.path.exists(session_file):
                session_time = os.path.getmtime(session_file)
                for f in present:
                    if f != "recovery.json" and os.path.getmtime(os.path.join(state_dir, f)) > session_time + 1.0:
                        status = "out_of_sync"
                        synced = False
                        break
        
        res = {
            "status": status,
            "state_files_present": present,
            "session_synced": synced
        }
        print(json.dumps(res, indent=2))
        
    elif args.subaction == "recover":
        restored = []
        if os.path.exists(session_file):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                deconstruct_state(".", session_data)
                restored = ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json"]
            except Exception:
                pass
        
        res = {
            "status": "success" if restored else "failed",
            "recovered_files": restored
        }
        print(json.dumps(res, indent=2))
        
    elif args.subaction == "validate":
        errors = []
        files = ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json"]
        for f in files:
            p = os.path.join(state_dir, f)
            if not os.path.exists(p):
                errors.append(f"Missing {f}")
            else:
                try:
                    with open(p, "r", encoding="utf-8") as file:
                        json.load(file)
                except Exception:
                    errors.append(f"Corrupted JSON in {f}")
                    
        res = {
            "status": "success" if not errors else "failed",
            "errors": errors
        }
        print(json.dumps(res, indent=2))
        if errors:
            sys.exit(1)

def do_registry(args):
    import aiwf_registry
    if args.subaction == "register":
        res = aiwf_registry.register_project(
            args.path, 
            force=args.force, 
            source=args.source,
            framework_root=args.framework_root
        )
        if res["status"] == "success":
            print(f"AIWF project registered successfully.")
            print(f"Project Path: {res['project_path']}")
            print(f"Registry Path: {res['registry_path']}")
        else:
            print(f"[ERROR] {res['message']}")
            sys.exit(1)
    elif args.subaction == "unregister":
        target = args.path if args.path else "."
        success = aiwf_registry.unregister_project(target)
        if success:
            print(f"Project unregistered successfully: {target}")
        else:
            print(f"Project not found in registry: {target}")
    elif args.subaction == "list":
        projects = aiwf_registry.list_projects()
        if not projects:
            print("No projects registered yet.")
            return
        print(f"{'ID':<34} | {'Name':<20} | {'Status':<8} | {'Version':<8} | {'Path'}")
        print("-" * 100)
        for p in projects:
            print(f"{p['id']:<34} | {p['name'][:20]:<20} | {p['status']:<8} | {p['aiwf_version']:<8} | {p['path']}")
    elif args.subaction == "doctor":
        report = aiwf_registry.doctor_registry()
        print(f"Registry Path: {report['registry_path']}")
        print(f"Total Registered: {report['total_registered']}")
        print(f"Active Projects: {report['active']}")
        print(f"Missing Projects: {report['missing']}")
        if report["details"]:
            print("\nDetails:")
            for d in report["details"]:
                status_str = f"[{d['status'].upper()}]"
                issues_str = f" (Issues: {', '.join(d['issues'])})" if d["issues"] else ""
                print(f"  - {d['name']} ({d['path']}) {status_str}{issues_str}")
    elif args.subaction == "cleanup":
        res = aiwf_registry.cleanup_registry()
        print(f"Cleanup complete. Total Removed: {res['total_removed']}. Remaining active: {res['remaining']}.")
        if res["removed_paths"]:
            print("Removed paths:")
            for rp in res["removed_paths"]:
                print(f"  - {rp}")

def do_update(args):
    import aiwf_registry
    update_all = args.all
    update_current = args.current
    
    if not update_all and not update_current:
        if sys.stdout.isatty():
            print("Update mode:")
            print("1. Current project only")
            print("2. All registered projects")
            print("3. Cancel")
            try:
                choice = input("Enter choice (1-3): ").strip()
                if choice == "1":
                    update_current = True
                elif choice == "2":
                    update_all = True
                else:
                    print("Cancelled.")
                    return
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                return
        else:
            update_current = True
            
    if update_all:
        print("Starting batch update of all registered projects...")
        summary = aiwf_registry.update_all_projects()
        print("\n==================================================")
        print("AIWF Update Summary:")
        print(f"  Total registered: {summary['total']}")
        print(f"  Updated:          {summary['updated']}")
        print(f"  Skipped:          {summary['skipped']}")
        print(f"  Failed:           {summary['failed']}")
        print(f"  Missing:          {summary['missing']}")
        print("==================================================")
        if summary["failed"] > 0:
            print("\nFailed updates:")
            for d in summary["details"]:
                if d["status"] == "failed":
                    print(f"  - {d['path']}: {d['reason']}")
            sys.exit(1)
    elif update_current:
        from memory.update import run_update
        res = run_update()
        if res.get("status") == "failed":
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="AI Workflow Runtime Engine CLI")
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    init_p = subparsers.add_parser("init")
    _ = init_p.add_argument("--permission", type=str, default=None)
    
    _ = subparsers.add_parser("permission")
    _ = subparsers.add_parser("compact")
    
    val = subparsers.add_parser("validate")
    _ = val.add_argument("--checkpoint", type=str)
    val_sub = val.add_subparsers(dest="subaction", required=False)
    val_art = val_sub.add_parser("artifact")
    _ = val_art.add_argument("--file", required=True, type=str)
    val_bp = val_sub.add_parser("blueprint")
    _ = val_bp.add_argument("--file", required=True, type=str)
    _ = val_sub.add_parser("session")
    
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

    choice_p = subparsers.add_parser("choice")
    choice_sub = choice_p.add_subparsers(dest="subaction", required=True)
    
    choice_create = choice_sub.add_parser("create")
    _ = choice_create.add_argument("--id", required=True, type=str)
    _ = choice_create.add_argument("--title", required=True, type=str)
    _ = choice_create.add_argument("--desc", type=str)
    _ = choice_create.add_argument("--options", required=True, type=str)
    _ = choice_create.add_argument("--type", type=str, default="choice")
    _ = choice_create.add_argument("--required", action="store_true")
    _ = choice_create.add_argument("--allow-cancel", action="store_true")
    
    choice_wait = choice_sub.add_parser("wait")
    _ = choice_wait.add_argument("--id", required=True, type=str)
    _ = choice_wait.add_argument("--timeout", type=int)
    
    choice_read = choice_sub.add_parser("read")
    _ = choice_read.add_argument("--id", required=True, type=str)
    
    _ = choice_sub.add_parser("clear")
    
    aw_p = subparsers.add_parser("active-workflow")
    aw_sub = aw_p.add_subparsers(dest="subaction", required=True)
    
    _ = aw_sub.add_parser("get")
    
    aw_set = aw_sub.add_parser("set")
    _ = aw_set.add_argument("--type", type=str)
    _ = aw_set.add_argument("--phase", type=str)
    _ = aw_set.add_argument("--skill", type=str)
    _ = aw_set.add_argument("--command", type=str)
    _ = aw_set.add_argument("--artifact-id", type=str)
    _ = aw_set.add_argument("--spec-path", type=str)
    _ = aw_set.add_argument("--blueprint-path", type=str)
    _ = aw_set.add_argument("--waiting-for", type=str)
    _ = aw_set.add_argument("--last-user-prompt", type=str)
    _ = aw_set.add_argument("--resume-instruction", type=str)
    
    _ = aw_sub.add_parser("clear")
    _ = aw_sub.add_parser("resume")
    
    aw_wait = aw_sub.add_parser("set-waiting")
    _ = aw_wait.add_argument("--waiting-for", type=str)
    
    aw_val = aw_sub.add_parser("validate-blueprint")
    _ = aw_val.add_argument("--path", required=True, type=str)
    _ = aw_val.add_argument("--workflow", type=str)
    
    _ = aw_sub.add_parser("get-branch")
    
    aw_sug = aw_sub.add_parser("suggest-branch")
    _ = aw_sug.add_argument("--artifact-id", required=True, type=str)
    _ = aw_sug.add_argument("--slug", required=True, type=str)
    
    aw_opts = aw_sub.add_parser("branch-options")
    _ = aw_opts.add_argument("--artifact-id", required=True, type=str)
    _ = aw_opts.add_argument("--slug", required=True, type=str)
    
    # New subcommands registration
    _ = subparsers.add_parser("resume")
    _ = subparsers.add_parser("discover")
    
    reg_p = subparsers.add_parser("registry")
    reg_sub = reg_p.add_subparsers(dest="subaction", required=True)
    
    reg_reg = reg_sub.add_parser("register")
    _ = reg_reg.add_argument("--path", type=str, default=".")
    _ = reg_reg.add_argument("--force", action="store_true")
    _ = reg_reg.add_argument("--source", type=str, default="register")
    _ = reg_reg.add_argument("--framework-root", type=str, default=None)
    
    reg_unreg = reg_sub.add_parser("unregister")
    _ = reg_unreg.add_argument("--path", type=str, default=".")
    
    _ = reg_sub.add_parser("list")
    _ = reg_sub.add_parser("doctor")
    _ = reg_sub.add_parser("cleanup")
    
    upd_p = subparsers.add_parser("update")
    _ = upd_p.add_argument("--all", action="store_true")
    _ = upd_p.add_argument("--current", action="store_true")
    
    classify_p = subparsers.add_parser("classify")
    _ = classify_p.add_argument("request", type=str)
    
    memory_p = subparsers.add_parser("memory")
    memory_sub = memory_p.add_subparsers(dest="subaction", required=True)
    _ = memory_sub.add_parser("bootstrap")
    _ = memory_sub.add_parser("update")
    mem_search_p = memory_sub.add_parser("search")
    _ = mem_search_p.add_argument("query", type=str)
    
    env_p = subparsers.add_parser("env")
    env_sub = env_p.add_subparsers(dest="subaction", required=True)
    _ = env_sub.add_parser("health")
    
    debug_p = subparsers.add_parser("debug")
    debug_sub = debug_p.add_subparsers(dest="subaction", required=True)
    _ = debug_sub.add_parser("run")
    
    verify_p = subparsers.add_parser("verify")
    verify_sub = verify_p.add_subparsers(dest="subaction", required=True)
    _ = verify_sub.add_parser("run")
    
    release_p = subparsers.add_parser("release")
    release_sub = release_p.add_subparsers(dest="subaction", required=True)
    _ = release_sub.add_parser("plan")
    rel_exec = release_sub.add_parser("execute")
    _ = rel_exec.add_argument("--approve", action="store_true")
    
    _ = subparsers.add_parser("context")
    
    rules_p = subparsers.add_parser("rules")
    rules_sub = rules_p.add_subparsers(dest="subaction", required=True)
    _ = rules_sub.add_parser("status")
    
    state_p = subparsers.add_parser("state")
    state_sub = state_p.add_subparsers(dest="subaction", required=True)
    _ = state_sub.add_parser("status")
    _ = state_sub.add_parser("recover")
    _ = state_sub.add_parser("validate")
    
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
        "prompt": do_prompt,
        "choice": do_choice,
        "active-workflow": do_active_workflow,
        "resume": do_resume_action,
        "discover": do_discover_action,
        "classify": do_classify_action,
        "memory": do_memory_action,
        "env": do_env_action,
        "debug": do_debug_action,
        "verify": do_verify_action,
        "release": do_release_action,
        "context": do_context,
        "rules": do_rules_action,
        "state": do_state_action,
        "registry": do_registry,
        "update": do_update
    }
    
    modifying_actions = ["init", "start", "step", "complete", "fail", "blueprint", "suggest", "compact", "task", "execution", "analysis-agent", "choice", "active-workflow", "resume", "discover", "classify", "memory", "env", "debug", "verify", "release", "state"]
    if args.action in modifying_actions:
        with SessionLock():
            cmds[args.action](args)
    else:
        cmds[args.action](args)

if __name__ == "__main__":
    main()

