import os
import json
import tempfile
import hashlib
from datetime import datetime
from typing import Any

def write_json_atomic(file_path: str, data: dict[str, Any]) -> None:
    dir_name = os.path.dirname(file_path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, file_path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise e

def read_json_safe(file_path: str) -> dict[str, Any]:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                raise ValueError("Empty file")
            res = json.loads(content)
            if not isinstance(res, dict):
                raise ValueError("Not a dictionary")
            return res
    except Exception:
        return {}

def calculate_checksum(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return ""

def aggregate_state(workspace_root: str) -> dict[str, Any]:
    state_dir = os.path.join(workspace_root, ".agents", "state")
    session_path = os.path.join(workspace_root, ".agents", ".session.json")
    
    context = read_json_safe(os.path.join(state_dir, "context.json"))
    workflow = read_json_safe(os.path.join(state_dir, "workflow.json"))
    runtime = read_json_safe(os.path.join(state_dir, "runtime.json"))
    approvals = read_json_safe(os.path.join(state_dir, "approvals.json"))
    usage = read_json_safe(os.path.join(state_dir, "usage.json"))
    agents = read_json_safe(os.path.join(state_dir, "agents.json"))
    
    session = {
        "workspace": {
            "path": context.get("workspace_path", "."),
            "valid": True
        },
        "git": context.get("git", {
            "is_git_repository": False,
            "branch": "unknown",
            "working_tree": "unknown",
            "default_branch": "unknown",
            "latest_tag": "none"
        }),
        "work_item": workflow.get("work_item", {
            "type": "None",
            "id": "None",
            "title": "None"
        }),
        "version": {
            "version": context.get("project_version", "1.0.0"),
            "source": context.get("version_source", "none")
        },
        "memory": context.get("memory", {
            "status": "MISSING",
            "last_updated": "N/A"
        }),
        "rag": context.get("rag", {
            "connected": False,
            "provider": "none"
        }),
        "blueprint": approvals.get("blueprint", {
            "path": "",
            "exists": False,
            "approved": False,
            "approved_at": "",
            "approved_by": ""
        }),
        "suggestion_gate": {
            "active": runtime.get("suggestion_gate", {}).get("active", False) if isinstance(runtime.get("suggestion_gate"), dict) else False,
            "raw_request": runtime.get("suggestion_gate", {}).get("raw_request", "") if isinstance(runtime.get("suggestion_gate"), dict) else "",
            "classification": runtime.get("suggestion_gate", {}).get("classification", "") if isinstance(runtime.get("suggestion_gate"), dict) else "",
            "recommended_skill": runtime.get("suggestion_gate", {}).get("recommended_skill", "") if isinstance(runtime.get("suggestion_gate"), dict) else "",
            "options": runtime.get("suggestion_gate", {}).get("options", []) if isinstance(runtime.get("suggestion_gate"), dict) else [],
            "status": runtime.get("suggestion_gate", {}).get("status", "idle") if isinstance(runtime.get("suggestion_gate"), dict) else "idle"
        },
        "checkpoint": workflow.get("checkpoint", 1),
        "active_workflow": workflow.get("active_workflow"),
        "active_phase": workflow.get("active_phase"),
        "waiting_for": workflow.get("waiting_for"),
        "resume_state": workflow.get("resume_state"),
        "status": runtime.get("status", "in_progress"),
        "current_skill": runtime.get("current_skill", "initialize-workflow"),
        "current_command": runtime.get("current_command", "init"),
        "current_step": runtime.get("current_step", "Starting workflow initialization..."),
        "current_logs": runtime.get("current_logs", []),
        "suggested_next_skill": workflow.get("suggested_next_skill"),
        "suggested_next_command": workflow.get("suggested_next_command"),
        "context_health": runtime.get("context_health", "healthy"),
        "pending_input": runtime.get("pending_input"),
        "permission_mode": context.get("permission_mode", "sandbox"),
        "permission_mode_selected_at": context.get("permission_mode_selected_at"),
        "permission_mode_selected_by": context.get("permission_mode_selected_by"),
        "conversation_id": context.get("conversation_id", ""),
        "project_fingerprint": context.get("project_fingerprint", ""),
        "workflow_usage_summary": usage.get("workflow_usage_summary", {}),
        "project_usage_summary": usage.get("project_usage_summary", {}),
        "global_usage_summary": usage.get("global_usage_summary", {}),
        "context_usage": usage.get("context_usage", {}),
        "telemetry_config": runtime.get("telemetry_config", {}),
        "updated_at": runtime.get("updated_at") or datetime.now().astimezone().isoformat(),
        "execution_mode": "sequential" if agents.get("execution_mode", "sequential") == "parallel" else agents.get("execution_mode", "sequential"),
        "recommended_mode": "sequential" if agents.get("recommended_mode", "sequential") == "parallel" else agents.get("recommended_mode", "sequential"),
        "approved": agents.get("approved", True),
        "parallel_groups": [],
        "running_agents": agents.get("running_agents", []),
        "queued_agents": agents.get("queued_agents", []),
        "blocked_agents": agents.get("blocked_agents", []),
        "waiting_dependencies": agents.get("waiting_dependencies", []),
        "analysis_agents": agents.get("analysis_agents", [])
    }
    
    # Clean None values for compatibility with test assertions
    for k in ["active_workflow", "active_phase", "waiting_for", "suggested_next_skill", "suggested_next_command"]:
        if k in session and session[k] is None:
            del session[k]
            
    # In Pure Split State mode, we do not write .session.json to disk.
    update_recovery_file(workspace_root)
    return session

def deconstruct_state(workspace_root: str, session: dict[str, Any]) -> None:
    state_dir = os.path.join(workspace_root, ".agents", "state")
    os.makedirs(state_dir, exist_ok=True)
    
    context = {
        "project_id": session.get("workspace", {}).get("project_id", "ai-skill-framework"),
        "workspace_path": session.get("workspace", {}).get("path", "."),
        "project_type": session.get("workspace", {}).get("project_type", "python"),
        "languages": session.get("workspace", {}).get("languages", ["python"]),
        "frameworks": session.get("workspace", {}).get("frameworks", []),
        "git": session.get("git", {}),
        "project_version": session.get("version", {}).get("version", "1.0.0"),
        "version_source": session.get("version", {}).get("source", "none"),
        "memory": session.get("memory", {}),
        "rag": session.get("rag", {}),
        "permission_mode": session.get("permission_mode", "sandbox"),
        "permission_mode_selected_at": session.get("permission_mode_selected_at"),
        "permission_mode_selected_by": session.get("permission_mode_selected_by"),
        "conversation_id": session.get("conversation_id", ""),
        "project_fingerprint": session.get("project_fingerprint", ""),
        "initialized_at": session.get("initialized_at") or datetime.now().astimezone().isoformat()
    }
    
    workflow = {
        "active_workflow": session.get("active_workflow"),
        "active_phase": session.get("active_phase"),
        "checkpoint": session.get("checkpoint", 1),
        "waiting_for": session.get("waiting_for"),
        "work_item": session.get("work_item", {}),
        "suggested_next_skill": session.get("suggested_next_skill"),
        "suggested_next_command": session.get("suggested_next_command"),
        "resume_state": session.get("resume_state", {})
    }
    
    runtime = {
        "current_skill": session.get("current_skill", "initialize-workflow"),
        "current_command": session.get("current_command", "init"),
        "current_step": session.get("current_step", "Initialization Complete"),
        "current_logs": session.get("current_logs", []),
        "status": session.get("status", "completed"),
        "context_health": session.get("context_health", "healthy"),
        "pending_input": session.get("pending_input"),
        "suggestion_gate": session.get("suggestion_gate", {}),
        "telemetry_config": session.get("telemetry_config", {}),
        "updated_at": session.get("updated_at")
    }
    
    approvals = {
        "blueprint": session.get("blueprint", {}),
        "specification": session.get("specification", {}),
        "branch_selected": session.get("branch_selected", {}),
        "release": session.get("release", {})
    }
    
    usage = {
        "workflow_usage_summary": session.get("workflow_usage_summary", {}),
        "project_usage_summary": session.get("project_usage_summary", {}),
        "global_usage_summary": session.get("global_usage_summary", {}),
        "context_usage": session.get("context_usage", {})
    }
    
    agents = {
        "execution_mode": "sequential" if session.get("execution_mode", "sequential") == "parallel" else session.get("execution_mode", "sequential"),
        "recommended_mode": "sequential" if session.get("recommended_mode", "sequential") == "parallel" else session.get("recommended_mode", "sequential"),
        "approved": session.get("approved", True),
        "parallel_groups": [],
        "running_agents": session.get("running_agents", []),
        "queued_agents": session.get("queued_agents", []),
        "blocked_agents": session.get("blocked_agents", []),
        "waiting_dependencies": session.get("waiting_dependencies", []),
        "analysis_agents": session.get("analysis_agents", [])
    }
    
    write_json_atomic(os.path.join(state_dir, "context.json"), context)
    write_json_atomic(os.path.join(state_dir, "workflow.json"), workflow)
    write_json_atomic(os.path.join(state_dir, "runtime.json"), runtime)
    write_json_atomic(os.path.join(state_dir, "approvals.json"), approvals)
    write_json_atomic(os.path.join(state_dir, "usage.json"), usage)
    write_json_atomic(os.path.join(state_dir, "agents.json"), agents)
    
    update_recovery_file(workspace_root)

def update_recovery_file(workspace_root: str) -> None:
    state_dir = os.path.join(workspace_root, ".agents", "state")
    recovery_path = os.path.join(state_dir, "recovery.json")
    
    checksums = {}
    for file_name in ["context.json", "workflow.json", "runtime.json", "approvals.json", "usage.json", "agents.json", "rules.json"]:
        file_path = os.path.join(state_dir, file_name)
        if os.path.exists(file_path):
            checksums[file_name] = calculate_checksum(file_path)
            
    recovery = {
        "last_good_snapshot_at": datetime.now().astimezone().isoformat(),
        "checksums": checksums,
        "recovery_source": "session.json"
    }
    write_json_atomic(recovery_path, recovery)
