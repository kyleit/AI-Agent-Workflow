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
    # Auto-detect and sync current conversation_id and context usage
    from context import refresh_context_usage_for_active_conversation
    usage = refresh_context_usage_for_active_conversation(session)

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
    
    # 2. Save it to DBs if conversation_id exists
    conv_id = session.get("conversation_id")
    if conv_id:
        proj_id = get_project_id()
        skill = session.get("current_skill", "unknown")
        cmd = session.get("current_command", "unknown")
        try:
            save_usage_to_dbs(conv_id, proj_id, skill, cmd, usage)
        except Exception as e:
            print(f"Warning: could not save usage to DB: {e}", file=sys.stderr)
        try:
            from context import sync_request_history
            sync_request_history(conv_id, proj_id)
        except Exception as e:
            print(f"Warning: could not sync request history: {e}", file=sys.stderr)
        
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
        
    session["project_usage_summary"] = get_project_summary(get_project_id())
    session["global_usage_summary"] = get_global_summary()
    
    try:
        from session import load_workflow_config
        config = load_workflow_config()
    except Exception:
        config = {}
    session["telemetry_config"] = config.get("telemetry", {
        "context_thresholds": {
            "warning": 60,
            "high": 80,
            "critical": 95
        },
        "context_styles": {
            "healthy": { "color": "#10b981", "bg": "rgba(16, 185, 129, 0.1)", "border": "rgba(16, 185, 129, 0.3)", "icon": "🟢", "label": "Healthy" },
            "warning": { "color": "#f59e0b", "bg": "rgba(245, 158, 11, 0.1)", "border": "rgba(245, 158, 11, 0.3)", "icon": "🟡", "label": "Warning" },
            "high": { "color": "#f97316", "bg": "rgba(249, 115, 22, 0.1)", "border": "rgba(249, 115, 22, 0.3)", "icon": "🟠", "label": "High" },
            "critical": { "color": "#ef4444", "bg": "rgba(239, 68, 68, 0.1)", "border": "rgba(239, 68, 68, 0.3)", "icon": "🔴", "label": "Critical" }
        },
        "cost_thresholds": {
            "warning_usd": 50.0,
            "critical_usd": 100.0
        }
    })
    
    # 4. Populate backward-compatible context_usage object
    session["context_usage"] = {
        "total_tokens": usage.get("active_tokens", 0),
        "limit_tokens": usage.get("limit_tokens", 2000000),
        "percentage": usage.get("percentage", 0.0)
    }
    
    # 5. Check drift
    drifted, msg = check_context_drift(session)
    session["context_health"] = "broken" if drifted else "healthy"
    
    # 6. Generate Context Breakdown state
    try:
        from breakdown_engine import update_breakdown_file
        update_breakdown_file(session, ".")
    except Exception:
        pass

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
                "2. Full Access Mode (Allow normal workflow file/code changes.)"
            ],
            default="1. Sandbox Mode (Safe default. Ask before every state-changing action.)"
        )
        if "2" in choice or "Full Access" in choice:
            permission_arg = "2"
        else:
            permission_arg = "1"
            
    if str(permission_arg) in ["2", "full_access"]:
        mode = "full_access"
    else:
        if str(permission_arg) in ["3", "unrestricted"]:
            print("Warning: Unrestricted mode is disabled for safety. Fallback to sandbox mode.")
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
    lock_file = os.path.join(".agents", "runtime", "workflow.lock")
    if os.path.exists(lock_file):
        print("Another workflow is already running.", file=sys.stderr)
        print("Do not continue.", file=sys.stderr)
        sys.exit(1)

    session = load_session()
    if not session:
        session = {"workspace": {"path": ".", "valid": True}}

    # Write new lock file
    try:
        os.makedirs(os.path.dirname(lock_file), exist_ok=True)
        work_item_id = session.get("work_item", {}).get("id", "unknown")
        with open(lock_file, "w", encoding="utf-8") as f:
            json.dump({
                "lock_owner": f"orchestrator|{args.skill}",
                "work_item_id": work_item_id,
                "skill": args.skill,
                "pid": os.getpid(),
                "started_at": datetime.now().astimezone().isoformat(),
                "heartbeat_at": datetime.now().astimezone().isoformat()
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    
    # Check blueprint approval before starting implementation
    is_impl = (args.skill == "blueprint-to-implementation") or (args.checkpoint is not None and args.checkpoint >= 6)
    if is_impl:
        bp = session.get("blueprint", {})
        if not bp.get("approved"):
            print("Error: Cannot start implementation. Technical Design Blueprint is not approved.", file=sys.stderr)
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except Exception:
                    pass
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
    lock_file = os.path.join(".agents", "runtime", "workflow.lock")
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r", encoding="utf-8") as f:
                lock_data = json.load(f)
            lock_data["heartbeat_at"] = datetime.now().astimezone().isoformat()
            with open(lock_file, "w", encoding="utf-8") as f:
                json.dump(lock_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

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
    lock_file = os.path.join(".agents", "runtime", "workflow.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass

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
    lock_file = os.path.join(".agents", "runtime", "workflow.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except Exception:
            pass

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
        
    elif args.subaction == "breakdown":
        update_context_health(session)
        from breakdown_engine import generate_breakdown
        bd = generate_breakdown(session, ".")
        
        print("\n==================================================================================")
        print("ACTIVE CONTEXT BREAKDOWN DIAGNOSTICS")
        print("==================================================================================")
        print(f"{'Context Source':<30} | {'Tokens':<10} | {'Percentage':<10} | {'Loads':<6} | {'Last Loaded Time':<25}")
        print("-" * 90)
        
        for item in bd.get("breakdown", []):
            token_str = f"{item['tokens']:,}"
            pct_str = f"{item['percentage']:.2f}%"
            print(f"{item['category']:<30} | {token_str:<10} | {pct_str:<10} | {item['loads']:<6} | {item['last_loaded']:<25}")
            
        print("-" * 90)
        total_str = f"{bd.get('total_tokens', 0):,}"
        print(f"{'Total Active Context':<30} | {total_str:<10} | {'100.00%':<10} | {'':<6} | {'':<25}")
        print("==================================================================================\n")
        
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
            
    elif args.subaction == "requests":
        filters = {}
        
        proj_filter = args.project
        if proj_filter == "current":
            proj_filter = get_project_id()
        if proj_filter:
            filters["project_id"] = proj_filter
            
        wf_filter = args.workflow
        if wf_filter == "current":
            wf_filter = session.get("conversation_id")
        if wf_filter:
            filters["workflow_id"] = wf_filter
            
        if args.skill:
            filters["skill_name"] = args.skill
        if args.model:
            filters["model"] = args.model
        if args.provider:
            filters["provider"] = args.provider
        if args.status:
            filters["status"] = args.status
        if args.start_time:
            filters["start_time"] = args.start_time
        if args.end_time:
            filters["end_time"] = args.end_time
            
        sort_by = "timestamp"
        desc = True
        limit = None
        
        if args.top_cost:
            sort_by = "cost_usd"
            limit = args.top_cost
        elif args.top_input:
            sort_by = "input_tokens"
            limit = args.top_input
            
        from db import get_provider_requests
        reqs = get_provider_requests(filters, sort_by=sort_by, desc=desc, limit=limit)
        
        if args.format == "json":
            print(json.dumps(reqs, indent=2))
        else:
            header = f"{'Request ID':<36} | {'Skill':<18} | {'Status':<8} | {'Tokens':<8} | {'Cost USD':<10} | {'Duration':<8}"
            print(header)
            print("-" * len(header))
            for r in reqs:
                cost_str = f"${r['cost_usd']:.4f}"
                tokens_str = f"{r['total_tokens']:,}"
                duration_str = f"{r['duration']:.2f}s"
                print(f"{r['request_id']:<36} | {r['skill_name']:<18} | {r['status']:<8} | {tokens_str:<8} | {cost_str:<10} | {duration_str:<8}")
                
    elif args.subaction == "request":
        if not args.id:
            print("Error: --id is required for request subcommand.", file=sys.stderr)
            sys.exit(1)
            
        from db import get_provider_request_detail
        r = get_provider_request_detail(args.id)
        if not r:
            print(f"Error: Request with ID '{args.id}' not found.", file=sys.stderr)
            sys.exit(1)
            
        if args.format == "json":
            print(json.dumps(r, indent=2))
        else:
            print(f"Request Audit Detail:")
            print(f"--------------------")
            print(f"ID:           {r['request_id']}")
            print(f"Workflow:     {r['workflow_id']}")
            print(f"Project:      {r['project_id']}")
            print(f"Skill/Cmd:    {r['skill_name']} / {r['command_name']}")
            print(f"Model/Prov:   {r['model']} ({r['provider']})")
            print(f"Timestamp:    {r['timestamp']}")
            print(f"Duration:     {r['duration']:.2f}s")
            print(f"Status:       {r['status'].upper()}")
            if r['error_summary']:
                print(f"Error:        {r['error_summary']}")
            print(f"Tokens:       Total={r['total_tokens']:,} (Input={r['input_tokens']:,}, Output={r['output_tokens']:,}, Cache={r['cache_tokens']:,}, Thinking={r['thinking_tokens']:,})")
            print(f"Cost:         ${r['cost_usd']:.6f} USD")
            print(f"Stats:        Tools={r['tool_call_count']}, Reads={r['workspace_read_count']}, Memory Hits={r['memory_hit_count']}, RAG Hits={r['rag_hit_count']}")
            print(f"Context:      {r['context_usage_percentage']:.2f}% (Limit={r['context_limit_tokens']:,})")
            
            if r['context_breakdown_json']:
                try:
                    cb = json.loads(r['context_breakdown_json'])
                    print(f"\nContext Breakdown:")
                    print(f"{'Category':<25} | {'Tokens':<10} | {'Percentage':<10}")
                    print("-" * 50)
                    for item in cb.get("breakdown", []):
                        print(f"{item['category']:<25} | {item['tokens']:<10,} | {item['percentage']:.1f}%")
                except Exception:
                    pass
            
    elif args.subaction == "diff":
        from db import get_provider_requests, get_provider_request_detail
        from diff_engine import calculate_diff
        
        req_a = None
        req_b = None
        
        if getattr(args, "latest", False):
            conv_id = session.get("conversation_id", "")
            reqs = get_provider_requests({"conversation_id": conv_id}, sort_by="timestamp", desc=True, limit=2)
            if len(reqs) < 2:
                print("Error: Need at least 2 requests in conversation to perform diff.", file=sys.stderr)
                sys.exit(1)
            req_b = reqs[0] # current
            req_a = reqs[1] # previous
        else:
            if not args.id_a:
                print("Error: --id-a is required for diff subcommand.", file=sys.stderr)
                sys.exit(1)
            
            req_b = get_provider_request_detail(args.id_b) if args.id_b else None
            req_a = get_provider_request_detail(args.id_a)
            
            if not req_a:
                print(f"Error: Request with ID '{args.id_a}' not found.", file=sys.stderr)
                sys.exit(1)
                
            if not req_b:
                conv_id = req_a.get("conversation_id")
                reqs = get_provider_requests({"conversation_id": conv_id}, sort_by="timestamp", desc=True)
                idx = -1
                for i, r in enumerate(reqs):
                    if r["request_id"] == req_a["request_id"]:
                        idx = i
                        break
                if idx != -1 and idx + 1 < len(reqs):
                    req_b = req_a
                    req_a = reqs[idx + 1]
                else:
                    req_b = req_a
                    req_a = None
                    
        cb_a = {}
        if req_a and req_a.get("context_breakdown_json"):
            try:
                cb_a = json.loads(req_a["context_breakdown_json"]) if isinstance(req_a["context_breakdown_json"], str) else req_a["context_breakdown_json"]
            except Exception:
                cb_a = {}
                
        cb_b = {}
        if req_b and req_b.get("context_breakdown_json"):
            try:
                cb_b = json.loads(req_b["context_breakdown_json"]) if isinstance(req_b["context_breakdown_json"], str) else req_b["context_breakdown_json"]
            except Exception:
                cb_b = {}
                
        diff = calculate_diff(cb_a, cb_b)
        
        if args.format == "json":
            print(json.dumps(diff, indent=2))
        else:
            print("\n==================================================================================")
            print("TOKEN CONTEXT DIFF DIAGNOSTICS")
            print("==================================================================================")
            print(f"Previous Request: {diff.get('previous_request_id')}")
            print(f"Current Request:  {diff.get('current_request_id')}")
            print(f"Net Change:       {diff.get('net_change_tokens'):+,} tokens ({diff.get('percentage_change'):+.2f}%)")
            print(f"Added Tokens:     {diff.get('added_tokens'):,}")
            print(f"Removed Tokens:   {diff.get('removed_tokens'):,}")
            print("-" * 90)
            print(f"{'Category':<30} | {'Previous':<12} | {'Current':<12} | {'Delta':<12} | {'Percentage':<10}")
            print("-" * 90)
            for cat, data in diff.get("categories", {}).items():
                prev_str = f"{data['previous']:,}"
                curr_str = f"{data['current']:,}"
                delta_str = f"{data['delta']:+,}"
                pct_str = f"{data['percentage']:+.2f}%"
                print(f"{cat:<30} | {prev_str:<12} | {curr_str:<12} | {delta_str:<12} | {pct_str:<10}")
            print("==================================================================================\n")

    elif args.subaction == "insights":
        from db import get_insight_snapshots
        conv_id = session.get("conversation_id", "")
        snaps = get_insight_snapshots(conv_id)
        if not snaps:
            from db import get_provider_requests, save_insight_snapshot
            from insights_engine import calculate_efficiency_score
            reqs = get_provider_requests({"conversation_id": conv_id})
            if reqs:
                eff_score = calculate_efficiency_score(reqs)
                avg_tok = int(sum(r["total_tokens"] for r in reqs) / len(reqs))
                avg_cst = round(sum(r["cost_usd"] for r in reqs) / len(reqs), 6)
                snap = {
                    "timestamp": datetime.now().astimezone().isoformat(),
                    "conversation_id": conv_id,
                    "efficiency_score": eff_score,
                    "avg_tokens": avg_tok,
                    "avg_cost": avg_cst,
                    "growth_trend": "stable",
                    "insight_data": {
                        "request_count": len(reqs),
                        "total_cost": round(sum(r["cost_usd"] for r in reqs), 4),
                        "total_tokens": sum(r["total_tokens"] for r in reqs)
                    }
                }
                save_insight_snapshot(snap)
                snaps = [snap]
                
        latest_snap = snaps[0] if snaps else {
            "efficiency_score": 100,
            "avg_tokens": 0,
            "avg_cost": 0.0,
            "growth_trend": "stable",
            "insight_data": {"request_count": 0, "total_cost": 0.0, "total_tokens": 0}
        }
        
        if args.format == "json":
            print(json.dumps(latest_snap, indent=2))
        else:
            print("\n==================================================================================")
            print("RUNTIME INSIGHTS REPORT")
            print("==================================================================================")
            print(f"Efficiency Score:          {latest_snap.get('efficiency_score')}/100")
            print(f"Average Tokens/Req:        {latest_snap.get('avg_tokens'):,}")
            print(f"Average Cost/Req:          ${latest_snap.get('avg_cost'):.6f} USD")
            print(f"Context Growth Trend:      {latest_snap.get('growth_trend').upper()}")
            print("-" * 90)
            idata = latest_snap.get("insight_data", {})
            print(f"Total Model Requests:      {idata.get('request_count')}")
            print(f"Total Cumulative Cost:     ${idata.get('total_cost', 0.0):.4f} USD")
            print(f"Total Cumulative Tokens:   {idata.get('total_tokens', 0):,}")
            print("==================================================================================\n")

    elif args.subaction == "recommendations":
        from db import get_recommendations
        conv_id = session.get("conversation_id", "")
        recs = get_recommendations(conv_id)
        if not recs:
            from db import get_provider_requests, save_recommendations
            from insights_engine import generate_recommendations
            reqs = get_provider_requests({"conversation_id": conv_id})
            recs = generate_recommendations(reqs, conv_id)
            if recs:
                save_recommendations(recs)
                
        if args.format == "json":
            print(json.dumps(recs, indent=2))
        else:
            print("\n==================================================================================")
            print("OPTIMIZATION RECOMMENDATIONS")
            print("==================================================================================")
            if not recs:
                print("No optimization recommendations found.")
            else:
                for r in recs:
                    status_lbl = r['status'].upper()
                    print(f"ID:          {r['id']} [{status_lbl}]")
                    print(f"Type:        {r['type']}")
                    print(f"Description: {r['description']}")
                    print(f"Savings:     Token Savings={r['token_savings']:,} | Cost Savings=${r['cost_savings']:.4f}")
                    print(f"Prio/Conf:   Priority={r['priority']} | Confidence={r['confidence']}")
                    print("-" * 90)
            print("==================================================================================\n")

    elif args.subaction == "optimize":
        if not args.accept and not args.ignore:
            from optimizer import calculate_roi, generate_benchmark_report, get_active_policy, set_active_policy, get_optimization_leaderboard
            conv_id = session.get("conversation_id", "")
            
            from context import estimate_context_usage
            usage = estimate_context_usage()
            predicted_tokens = usage.get("total_tokens", 0)
            predicted_cost = usage.get("estimated_cost_usd", 0.0)
            
            opt_sub = args.optimize_subaction
            
            if opt_sub == "analyze":
                res = calculate_roi(conv_id)
                leaderboard = get_optimization_leaderboard()
                result = {
                    "roi": res,
                    "leaderboard": leaderboard
                }
                if args.format == "json":
                    print(json.dumps(result, indent=2))
                else:
                    print("\n==================================================================================")
                    print("AUTONOMOUS OPTIMIZATION ROI ANALYSIS")
                    print("==================================================================================")
                    print(f"Total Tokens Saved:    {res['total_tokens_saved']:,} tokens")
                    print(f"Total API Cost Saved:  ${res['total_cost_saved_usd']:.4f} USD")
                    print(f"Estimated ROI:         {res['roi_pct']}% savings")
                    print("\nLeaderboard of Saved Resources:")
                    for idx, l in enumerate(leaderboard):
                        print(f"  {idx+1}. Skill: {l['skill']} | Saved: {l['tokens_saved']:,} tkn (${l['cost_saved']:.3f})")
                    print("==================================================================================\n")
                    
            elif opt_sub == "benchmark":
                res = generate_benchmark_report(predicted_tokens, predicted_cost)
                if args.format == "json":
                    print(json.dumps(res, indent=2))
                else:
                    print("\n==================================================================================")
                    print("OPTIMIZATION BENCHMARK REPORT")
                    print("==================================================================================")
                    print(f"Active Policy:          {res['policy_used']}")
                    print(f"Original Input size:   {res['original_tokens']:,} tokens (${res['original_cost']:.4f} USD)")
                    print(f"Optimized Input size:  {res['optimized_tokens']:,} tokens (${res['optimized_cost']:.4f} USD)")
                    print(f"Net Tokens Saved:      +{res['tokens_saved']:,} tokens")
                    print(f"Net Cost Saved:        ${res['cost_saved']:.4f} USD")
                    print("==================================================================================\n")
                    
            elif opt_sub == "policies":
                if args.policy:
                    set_active_policy(args.policy)
                policy = get_active_policy()
                if args.format == "json":
                    print(json.dumps(policy, indent=2))
                else:
                    print("\n==================================================================================")
                    print("ACTIVE OPTIMIZATION POLICY CONFIGURATION")
                    print("==================================================================================")
                    print(f"Policy Name:            {policy['name']}")
                    print(f"Context Rebuild:        {'ENABLED' if policy['context_rebuild_enabled'] else 'DISABLED'}")
                    print(f"Cache usage:            {'ENABLED' if policy['cache_enabled'] else 'DISABLED'}")
                    print(f"Compression Target:     {policy['compression_pct']}% savings")
                    print("==================================================================================\n")
                    
            elif opt_sub == "history":
                leaderboard = get_optimization_leaderboard()
                if args.format == "json":
                    print(json.dumps(leaderboard, indent=2))
                else:
                    print("Optimization history retrieved.")
                    
            elif opt_sub == "report":
                res = generate_benchmark_report(predicted_tokens, predicted_cost)
                if args.format == "json":
                    print(json.dumps(res, indent=2))
                else:
                    print("Benchmark report generated.")
            sys.exit(0)

        from db import update_recommendation_status
        success = False
        action_type = ""
        rec_id = ""
        
        if args.accept:
            rec_id = args.accept
            success = update_recommendation_status(rec_id, "accepted")
            action_type = "accepted"
        elif args.ignore:
            rec_id = args.ignore
            success = update_recommendation_status(rec_id, "ignored")
            action_type = "ignored"
            
        if not rec_id:
            print("Error: --accept <id> or --ignore <id> is required for optimize subcommand.", file=sys.stderr)
            sys.exit(1)
            
        if success:
            print(json.dumps({"status": "success", "recommendation_id": rec_id, "action": action_type}))
        else:
            print(json.dumps({"status": "error", "message": f"Recommendation ID '{rec_id}' not found."}), file=sys.stderr)
            sys.exit(1)

    elif args.subaction == "timeline":
        from db import get_timeline_events
        conv_id = session.get("conversation_id", "")
        events = get_timeline_events(conv_id)
        if not events:
            from context import sync_request_history
            sync_request_history(conv_id, session.get("project_id") or get_project_id())
            events = get_timeline_events(conv_id)
            
        if args.format == "json":
            print(json.dumps(events, indent=2))
        else:
            print("\n==================================================================================")
            print("WORKFLOW CONTEXT TIMELINE")
            print("==================================================================================")
            if not events:
                print("No workflow events logged yet.")
            else:
                for e in events:
                    print(f"[{e['timestamp']}] Checkpoint={e['checkpoint']} | Skill={e['skill']}")
                    print(f"  Event:      {e['event_type']}")
                    print(f"  Context:    Active={e['active_context']:,} tokens | Delta={e['context_delta']:+,} tokens")
                    print(f"  Details:    Cost=${e['cost']:.4f} USD | Duration={e['duration']:.1f}s")
                    print("-" * 90)
            print("==================================================================================\n")

    elif args.subaction == "forecast":
        from db import get_timeline_events
        from forecaster import make_forecast
        conv_id = session.get("conversation_id", "")
        events = get_timeline_events(conv_id)
        if not events:
            from context import sync_request_history
            sync_request_history(conv_id, session.get("project_id") or get_project_id())
            events = get_timeline_events(conv_id)
            
        report = make_forecast(events)
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print("\n==================================================================================")
            print("PREDICTIVE ANALYSIS & FORECAST")
            print("==================================================================================")
            print(f"Context Exhaustion Probability:  {report['exhaustion_probability'].upper()}")
            print(f"Prediction Confidence Level:    {report['confidence_level'].upper()}")
            print(f"Estimated Remaining Requests:   {report['remaining_requests']}")
            print(f"Predicted Context (Next Req):   {report['predicted_next_context']:,} tokens")
            print(f"Estimated Cost to Complete:     ${report['estimated_cost_to_complete']:.4f} USD")
            print("==================================================================================\n")

    elif args.subaction == "budget":
        from budget_controller import evaluate_budget, get_budget_history, apply_optimization
        conv_id = session.get("conversation_id", "")
        
        from context import estimate_context_usage
        usage = estimate_context_usage()
        predicted_tokens = usage.get("total_tokens", 0)
        
        budget_sub = args.budget_subaction
        
        if budget_sub == "status":
            result = evaluate_budget(conv_id, predicted_tokens)
            if args.format == "json":
                print(json.dumps(result, indent=2))
            else:
                print("\n==================================================================================")
                print("CONTEXT BUDGET STATUS")
                print("==================================================================================")
                print(f"Policy Triggered:       {result['policy_triggered']}")
                print(f"Status:                 {result['status'].upper()}")
                print(f"Predicted Context:      {predicted_tokens:,} tokens ({result['predicted_pct']}%)")
                print("\nThresholds:")
                for k, v in result["policy_thresholds"].items():
                    print(f"  - {k.replace('_', ' ').title()}: {v}%")
                
                print("\nRecommended Strategies:")
                if not result["recommendations"]:
                    print("  None (Context usage is within budget).")
                else:
                    for r in result["recommendations"]:
                        print(f"  - {r['name']} (Est. savings: +{r['tokens_saved']:,} tokens, Conf: {r['confidence']*100}%)")
                print("==================================================================================\n")
                
        elif budget_sub == "mode":
            from budget_controller import set_budget_mode, get_budget_mode
            if args.status in ["auto", "manual"]:
                set_budget_mode(args.status)
            cur_mode = get_budget_mode()
            res = {"status": "success", "budget_mode": cur_mode}
            if args.format == "json":
                print(json.dumps(res, indent=2))
            else:
                print(f"Budget controller mode: {cur_mode.upper()}")

        elif budget_sub == "history":
            history = get_budget_history(conv_id)
            if args.format == "json":
                print(json.dumps(history, indent=2))
            else:
                print("\n==================================================================================")
                print("CONTEXT BUDGET OPTIMIZATION HISTORY")
                print("==================================================================================")
                if not history:
                    print("No optimization actions applied yet.")
                else:
                    for h in history:
                        print(f"[{h['timestamp']}] Strategy: {h['strategy_applied']}")
                        print(f"  Saved: {h['tokens_saved']:,} tokens | Cost Saved: ${h['cost_saved']:.4f} USD")
                        print(f"  Status: {h['status'].upper()}")
                        print("-" * 90)
                print("==================================================================================\n")
                
        elif budget_sub == "optimize":
            if not args.strategy:
                print("Error: --strategy <name> is required for budget optimize command.", file=sys.stderr)
                sys.exit(1)
            res = apply_optimization(conv_id, args.strategy, predicted_tokens)
            if args.format == "json":
                print(json.dumps(res, indent=2))
            else:
                if res.get("status") == "success":
                    print(f"Successfully applied optimization strategy '{args.strategy}'. Saved {res['tokens_saved']:,} tokens.")
                else:
                    print(f"Error: {res.get('message')}", file=sys.stderr)
                    sys.exit(1)

    elif args.subaction == "context":
        from context_rebuilder import build_context_bundle, get_rebuild_history, get_cache_statistics
        conv_id = session.get("conversation_id", "")
        
        from context import estimate_context_usage
        usage = estimate_context_usage()
        predicted_tokens = usage.get("total_tokens", 0)
        
        ctx_sub = args.context_subaction
        
        if ctx_sub == "preview":
            res = build_context_bundle(conv_id, predicted_tokens)
            if args.format == "json":
                print(json.dumps(res, indent=2))
            else:
                print("\n==================================================================================")
                print("CONTEXT BUNDLE PREVIEW")
                print("==================================================================================")
                print(f"Original Context:      {res['original_tokens']:,} tokens")
                print(f"Rebuilt Context:       {res['rebuilt_tokens']:,} tokens")
                print(f"Estimated Savings:     +{res['tokens_saved']:,} tokens ({res['savings_pct']}%)")
                print("\nIncluded Sources:")
                for s in res["included_sources"]:
                    print(f"  [+] {s}")
                print("\nSkipped Sources:")
                for s in res["skipped_sources"]:
                    print(f"  [-] {s}")
                print("==================================================================================\n")
                
        elif ctx_sub == "rebuild":
            res = build_context_bundle(conv_id, predicted_tokens)
            if args.format == "json":
                print(json.dumps({"status": "rebuilt", "savings": res["tokens_saved"]}, indent=2))
            else:
                print(f"Context bundle rebuilt successfully! Saved {res['tokens_saved']:,} tokens.")
                
        elif ctx_sub == "cache":
            stats = get_cache_statistics()
            if args.format == "json":
                print(json.dumps(stats, indent=2))
            else:
                print("\n==================================================================================")
                print("RUNTIME CACHE STATISTICS")
                print("==================================================================================")
                print(f"Cached Source Files:    {stats['cached_files']}")
                print(f"Cache Hits:            {stats['hits']}")
                print(f"Cache Misses:          {stats['misses']}")
                print("==================================================================================\n")
                
        elif ctx_sub == "explain":
            res = build_context_bundle(conv_id, predicted_tokens)
            history = get_rebuild_history(conv_id)
            explanation = {
                "engine": "Smart Context Rebuilder",
                "savings_factor": "85% decrease",
                "reasoning": "Dữ liệu lịch sử chat cũ được thay thế bằng bản tóm tắt runtime summary. Các tệp Blueprint và Rules được cache hoàn toàn dựa trên hash.",
                "rebuilt_tokens": res["rebuilt_tokens"],
                "total_rebuilds": len(history)
            }
            if args.format == "json":
                print(json.dumps(explanation, indent=2))
            else:
                print(f"Context Rebuild Explanation: {explanation['reasoning']}")

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
    parallel_allowed = False

    if args.subaction == "recommend":
        if not args.mode or not args.reason:
            print("Error: --mode and --reason are required.", file=sys.stderr)
            sys.exit(1)
        # Force recommendations to sequential
        rec_mode = "sequential"
        rec_reason = "Parallel execution is completely disabled in this framework. Sequential execution only."
        plan["implementation_execution_mode"] = "pending"
        plan["parallel_allowed_phase"] = "implementation"
        plan["parallel_allowed"] = False
        plan["execution_mode"] = "pending"
        plan["recommended_mode"] = rec_mode
        plan["recommended_reason"] = rec_reason
        plan["approved"] = False
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"Recommended execution mode set to {rec_mode} (Reason: {rec_reason}).")
        
    elif args.subaction == "mode":
        if not args.mode:
            print("Error: --mode is required.", file=sys.stderr)
            sys.exit(1)
            
        if args.mode == "parallel":
            print("Error: Parallel execution mode is disabled. Only sequential execution is supported.", file=sys.stderr)
            sys.exit(1)
            
        plan["implementation_execution_mode"] = "sequential"
        plan["execution_mode"] = "sequential"
        if args.approve:
            plan["approved"] = True
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"Execution mode updated to sequential (Approved: {plan.get('approved')}).")
        
    elif args.subaction == "summary":
        summary_text = """================================================================================

Execution Plan Summary

This framework operates in a strict Sequential Workflow Engine mode.
No parallel worker pools or concurrent executions are allowed to prevent
state drift and write contamination.

================================================================================
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
            
    elif args.subaction == "diagnose":
        session = load_session()
        lock_file = os.path.join(".agents", "runtime", "workflow.lock")
        lock_owner = "None"
        locked_at = "N/A"
        active_task = "None"
        if os.path.exists(lock_file):
            try:
                with open(lock_file, "r", encoding="utf-8") as f:
                    lock_data = json.load(f)
                lock_owner = lock_data.get("skill", "unknown")
                locked_at = lock_data.get("started_at", "N/A")
                active_task = f"{lock_owner} ({lock_data.get('lock_owner', '')})"
            except Exception:
                lock_owner = "Corrupted"
        
        exec_mode = session.get("execution_mode", "sequential")
        
        diagnostics = {
            "execution_mode": exec_mode,
            "active_task": active_task,
            "queue_length": 0,
            "lock_owner": lock_owner,
            "locked_at": locked_at,
            "waiting_tasks": []
        }
        print(json.dumps(diagnostics, indent=2))

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
    _ = usg.add_argument("subaction", choices=["sync", "report", "diagnose", "export", "breakdown", "requests", "request", "diff", "insights", "recommendations", "optimize", "timeline", "forecast", "budget", "context"])
    _ = usg.add_argument("--format", default="table", choices=["json", "table"])
    _ = usg.add_argument("--out", type=str)
    _ = usg.add_argument("--workflow", type=str)
    _ = usg.add_argument("--project", type=str)
    _ = usg.add_argument("--top-cost", type=int)
    _ = usg.add_argument("--top-input", type=int)
    _ = usg.add_argument("--id", type=str)
    _ = usg.add_argument("--skill", type=str)
    _ = usg.add_argument("--model", type=str)
    _ = usg.add_argument("--provider", type=str)
    _ = usg.add_argument("--status", type=str)
    _ = usg.add_argument("--id-a", type=str)
    _ = usg.add_argument("--id-b", type=str)
    _ = usg.add_argument("--latest", action="store_true")
    _ = usg.add_argument("--accept", type=str)
    _ = usg.add_argument("--ignore", type=str)
    _ = usg.add_argument("--strategy", type=str)
    _ = usg.add_argument("--budget-subaction", default="status", choices=["status", "history", "optimize", "mode"])
    _ = usg.add_argument("--context-subaction", default="preview", choices=["bundle", "preview", "rebuild", "cache", "explain"])
    _ = usg.add_argument("--optimize-subaction", default="analyze", choices=["analyze", "benchmark", "history", "policies", "report"])
    _ = usg.add_argument("--policy", type=str)
    _ = usg.add_argument("--start-time", type=str)
    _ = usg.add_argument("--end-time", type=str)
    
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
    _ = state_sub.add_parser("diagnose")
    
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

