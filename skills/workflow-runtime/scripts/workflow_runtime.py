# workflow_runtime.py
import argparse
import sys
import os
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

def update_context_health(session: dict) -> None:
    session["context_usage"] = estimate_context_usage()
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
    update_context_health(session)
    save_session_atomic(session)
    print("Session initialized.")

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

def main():
    parser = argparse.ArgumentParser(description="AI Workflow Runtime Engine CLI")
    subparsers = parser.add_subparsers(dest="action", required=True)
    
    subparsers.add_parser("init")
    
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
    
    args = parser.parse_args()
    
    cmds = {
        "init": do_init,
        "validate": do_validate,
        "start": do_start,
        "step": do_step,
        "complete": do_complete,
        "fail": do_fail,
        "heartbeat": do_heartbeat
    }
    
    cmds[args.action](args)

if __name__ == "__main__":
    main()
