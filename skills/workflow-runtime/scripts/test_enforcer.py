# test_enforcer.py
import os
import sys
import json
import subprocess
from typing import Tuple, List, Any

# Backup original subprocess functions
_orig_run = subprocess.run
_orig_Popen = subprocess.Popen

def is_test_command(cmd: Any) -> bool:
    if not cmd:
        return False
    cmd_list = []
    if isinstance(cmd, str):
        cmd_list = cmd.split()
    elif isinstance(cmd, (list, tuple)):
        cmd_list = [str(c) for c in cmd]
    else:
        return False
        
    cmd_str = " ".join(cmd_list).lower()
    
    # 1. Executables patterns
    test_executables = [
        "pytest", "unittest", "vitest", "jest", "playwright", "cypress",
        "go test", "cargo test", "npm test", "npm run test", "pnpm test", "yarn test"
    ]
    for te in test_executables:
        if te in cmd_str:
            return True
            
    # 2. Script names patterns
    test_scripts = [
        "test_", "run_tests", "test.sh", "test.ps1", "test.py"
    ]
    for ts in test_scripts:
        if ts in cmd_str:
            return True
            
    # 3. Makefile/Taskfile test targets
    if "make" in cmd_str or "task" in cmd_str or "just" in cmd_str:
        if "test" in cmd_str:
            return True
            
    return False

def verify_tester_ownership(cmd: Any) -> Tuple[bool, str]:
    # Resolve path to state directory
    base_dir = os.environ.get("AIWF_BASE_DIR") or os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    state_dir = os.path.join(base_dir, ".agents", "state")
    if not os.path.exists(state_dir):
        # Fallback to local default path if not exist
        if not os.environ.get("AIWF_BASE_DIR"):
            state_dir = ".agents/state"
        
    tasks_path = os.path.join(state_dir, "tasks.json")
    agents_path = os.path.join(state_dir, "agents.json")
    
    if not os.path.exists(tasks_path):
        return False, "tasks.json ledger not found"
        
    try:
        with open(tasks_path, "r", encoding="utf-8") as f:
            tdata = json.load(f)
        tasks = tdata.get("tasks", {})
    except Exception as e:
        return False, f"Failed to parse tasks.json: {e}"
        
    agents = {}
    if os.path.exists(agents_path):
        try:
            with open(agents_path, "r", encoding="utf-8") as f:
                agents = json.load(f)
        except Exception:
            pass
            
    # Find a running test task
    running_test_tasks = []
    for tid, t in tasks.items():
        if t.get("status") == "running":
            role = t.get("role", "").lower()
            name = t.get("name", "").lower()
            if role in ["testing", "verification"] or "test" in name or "verify" in name or "qa" in name:
                running_test_tasks.append((tid, t))
                
    if not running_test_tasks:
        return False, "No active running test task found in tasks.json"
        
    # Check ownership of running test tasks
    for tid, t in running_test_tasks:
        assigned = t.get("assigned_agent")
        if not assigned:
            continue
        agent_meta = agents.get(assigned, {})
        agent_type = agent_meta.get("type", "")
        # A TESTER/QA agent has type "qa" or "tester" or ID match
        if agent_type in ["qa", "tester"] or assigned == "AGENT-TESTER-001" or "tester" in assigned.lower() or "qa" in assigned.lower():
            return True, f"Valid owner found: {assigned} for task {tid}"
            
    return False, "Running test task exists but is not owned by a QA or TESTER agent"

def patched_run(*args, **kwargs):
    cmd = args[0] if args else kwargs.get("args")
    if is_test_command(cmd):
        allowed, msg = verify_tester_ownership(cmd)
        if not allowed:
            err_msg = f"Policy Violation: Test execution blocked. Reason: {msg} (Command: {cmd})"
            # Log violation event to tasks log if possible
            print(f"❌ {err_msg}", file=sys.stderr)
            raise PermissionError(err_msg)
    return _orig_run(*args, **kwargs)

def patched_Popen(*args, **kwargs):
    cmd = args[0] if args else kwargs.get("args")
    if is_test_command(cmd):
        allowed, msg = verify_tester_ownership(cmd)
        if not allowed:
            err_msg = f"Policy Violation: Test execution blocked. Reason: {msg} (Command: {cmd})"
            print(f"❌ {err_msg}", file=sys.stderr)
            raise PermissionError(err_msg)
    return _orig_Popen(*args, **kwargs)

def patch_subprocess():
    subprocess.run = patched_run
    subprocess.Popen = patched_Popen
