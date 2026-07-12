import os
import json
import tempfile
import hashlib
from datetime import datetime
from typing import Any

def write_json_atomic(file_path: str, data: dict[str, Any]) -> None:
    from state_store import get_state_store
    key = os.path.splitext(os.path.basename(file_path))[0]
    get_state_store().set(key, data)

def read_json_safe(file_path: str) -> dict[str, Any]:
    from state_store import get_state_store
    key = os.path.splitext(os.path.basename(file_path))[0]
    return get_state_store().get(key)

def calculate_checksum(file_path: str) -> str:
    from state_store import get_state_store
    key = os.path.splitext(os.path.basename(file_path))[0]
    data = get_state_store().get(key)
    if not data:
        return ""
    try:
        content = json.dumps(data, sort_keys=True)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    except Exception:
        return ""

def aggregate_state(workspace_root: str) -> dict[str, Any]:
    from state_store import get_state_store
    store = get_state_store()
    
    context = store.get("context")
    workflow = store.get("workflow")
    runtime = store.get("runtime")
    approvals = store.get("approvals")
    usage = store.get("usage")
    agents = store.get("agents")
    
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
        "resume_state": workflow.get("resume_state"),
        "status": runtime.get("status", "in_progress"),
        "current_skill": runtime.get("current_skill", "initialize-workflow"),
        "current_command": runtime.get("current_command", "init"),
        "current_step": runtime.get("current_step", "Starting workflow initialization..."),
        "current_logs": runtime.get("current_logs", []),
        "suggested_next_skill": workflow.get("suggested_next_skill"),
        "suggested_next_command": workflow.get("suggested_next_command"),
        "context_health": runtime.get("context_health", "healthy"),
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
        "execution_mode": agents.get("execution_mode", "parallel"),
        "recommended_mode": agents.get("recommended_mode", "parallel"),
        "approved": agents.get("approved", True),
        "parallel_groups": [],
        "running_agents": agents.get("running_agents", []),
        "queued_agents": agents.get("queued_agents", []),
        "blocked_agents": agents.get("blocked_agents", []),
        "waiting_dependencies": agents.get("waiting_dependencies", []),
        "analysis_agents": agents.get("analysis_agents", [])
    }
    if workflow.get("active_workflow") is not None:
        session["active_workflow"] = workflow.get("active_workflow")
    if workflow.get("active_phase") is not None:
        session["active_phase"] = workflow.get("active_phase")
    if workflow.get("waiting_for") is not None:
        session["waiting_for"] = workflow.get("waiting_for")
        
    # Store revisions of each file for CAS compare-and-swap checks
    session["_revisions"] = {
        "context": context.get("_metadata", {}).get("revision", 0),
        "workflow": workflow.get("_metadata", {}).get("revision", 0),
        "runtime": runtime.get("_metadata", {}).get("revision", 0),
        "approvals": approvals.get("_metadata", {}).get("revision", 0),
        "usage": usage.get("_metadata", {}).get("revision", 0),
        "agents": agents.get("_metadata", {}).get("revision", 0)
    }
    
    # Clean None values for compatibility with test assertions
    for k in ["active_workflow", "active_phase", "waiting_for", "suggested_next_skill", "suggested_next_command"]:
        if k in session and session[k] is None:
            del session[k]
            
    # In Pure Split State mode, we do not write .session.json to disk.
    update_recovery_file(workspace_root)
    return session

def deconstruct_state(workspace_root: str, session: dict[str, Any]) -> None:
    from state_store import get_state_store
    store = get_state_store()
    
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
        "execution_mode": session.get("execution_mode", "parallel"),
        "recommended_mode": session.get("recommended_mode", "parallel"),
        "approved": session.get("approved", True),
        "parallel_groups": [],
        "running_agents": session.get("running_agents", []),
        "queued_agents": session.get("queued_agents", []),
        "blocked_agents": session.get("blocked_agents", []),
        "waiting_dependencies": session.get("waiting_dependencies", []),
        "analysis_agents": session.get("analysis_agents", [])
    }
    
    revisions = session.get("_revisions", {})
    
    store.set("context", context, expected_revision=revisions.get("context"))
    store.set("workflow", workflow, expected_revision=revisions.get("workflow"))
    store.set("runtime", runtime, expected_revision=revisions.get("runtime"))
    store.set("approvals", approvals, expected_revision=revisions.get("approvals"))
    store.set("usage", usage, expected_revision=revisions.get("usage"))
    store.set("agents", agents, expected_revision=revisions.get("agents"))
    
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


# ---------------------------------------------------------------------------
# FEAT-050: Lightweight Initialization Summary Writers
# ---------------------------------------------------------------------------

def write_initialization_summary(
    guardrail_hashes: dict[str, Any],
    git_state: dict[str, Any],
    checkpoint: int,
    resolved_dependencies: dict[str, Any],
    init_start_time: float,
    workspace_root: str = ".",
) -> None:
    """
    Write a lightweight initialization summary to .agents/state/context.json.
    Called at the end of initialize-workflow Step 6.

    Fields written:
    - guardrail_hashes
    - git (branch, working_tree, is_repository)
    - checkpoint
    - resolved_dependencies summary
    - init_completed_at (ISO-8601)
    - init_latency_ms
    """
    import time

    state_dir = os.path.join(workspace_root, ".agents", "state")
    context_path = os.path.join(state_dir, "context.json")

    # Read existing context to merge
    existing = read_json_safe(context_path)

    init_latency_ms = round((time.perf_counter() - init_start_time) * 1000, 1)

    existing.update({
        "guardrail_hashes": guardrail_hashes,
        "git": git_state,
        "checkpoint": checkpoint,
        "resolved_dependencies": resolved_dependencies,
        "init_completed_at": datetime.now().astimezone().isoformat(),
        "init_latency_ms": init_latency_ms,
        "workspace_path": ".",  # Always relative — no absolute paths
    })

    write_json_atomic(context_path, existing)

    # Write runtime.json completion
    runtime_path = os.path.join(state_dir, "runtime.json")
    runtime = read_json_safe(runtime_path)
    runtime.update({
        "status": "completed",
        "current_step": "Initialization Complete",
        "checkpoint": checkpoint,
        "updated_at": datetime.now().astimezone().isoformat(),
    })
    write_json_atomic(runtime_path, runtime)


def validate_no_heavy_init_operations(
    called_functions: list[str],
    workspace_root: str = ".",
) -> list[str]:
    """
    Audit a list of function names called during initialize-workflow.
    Raises a critical warning (does not block) if any forbidden heavy operation was called.

    Forbidden functions during initialize-workflow:
    - sync_request_history
    - parse_transcript
    - refresh_context_usage_for_active_conversation
    - load_memory_required (full project-summary.md load)
    - connect_rag / validate_rag (RAG connect)
    - scan_docs_directory (workspace scan)
    - get_version_from_manifest (manifest scan)
    - subprocess.run with git describe --tags, python --version, node --version, docker version

    Returns list of violations found.
    """
    FORBIDDEN_FUNCTIONS = {
        "sync_request_history",
        "parse_transcript",
        "refresh_context_usage_for_active_conversation",
        "load_memory_required",
        "connect_rag",
        "validate_rag",
        "scan_docs_directory",
        "get_version_from_manifest",
        # Subprocess forbidden patterns handled by naming convention
        "git_describe_tags",
        "python_version_check",
        "node_version_check",
        "docker_version_check",
    }

    violations = [fn for fn in called_functions if fn in FORBIDDEN_FUNCTIONS]

    if violations:
        print(
            f"\n⚠️  [FEAT-050 CRITICAL WARNING] Heavy init operations detected during initialize-workflow:\n"
            f"    Violations: {violations}\n"
            f"    These operations are FORBIDDEN during lightweight initialization.\n"
            f"    Please audit the initialize-workflow SKILL.md and remove the offending calls.\n",
            flush=True,
        )

    return violations
