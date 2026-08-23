from __future__ import annotations

import argparse
from typing import Any

from workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing import \
    do_workflow


def do_orchestrator(args: Any):
    import json
    import os
    import sys
    from datetime import datetime

    state_dir = os.path.join(".agents", "state", "orchestrator")

    def read_json_safe_local(file_path: str) -> dict[str, Any]:
        if not os.path.exists(file_path):
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def write_json_atomic_local(file_path: str, data: dict[str, Any]) -> bool:
        temp_path = file_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, file_path)
            return True
        except Exception:
            return False

    def log_event_local(event_type: str, message: str) -> None:
        events_path = os.path.join(state_dir, "events.jsonl")
        evt = {
            "timestamp": datetime.now().astimezone().isoformat(),
            "event_type": event_type,
            "message": message
        }
        try:
            with open(events_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(evt) + "\n")
        except Exception:
            pass

    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    action = getattr(args, "action", None)
    task_id = getattr(args, "task_id", None)
    lock_id = getattr(args, "lock_id", None)

    work_item = getattr(args, "work_item_id", None) or getattr(args, "work_item_opt", None) or getattr(args, "work_item", None) or "FEAT-111"

    if subaction == "run":
        print("Warning: 'orchestrator run' is DEPRECATED. Redirecting internally to 'workflow submit'...", file=sys.stderr)

        class ArgsMock(argparse.Namespace):
            def __init__(self, prompt: str) -> None:
                super().__init__()
                self.subaction = "submit"
                self.prompt = prompt

        mock_args = ArgsMock(prompt=f"Submitted via legacy orchestrator redirection for work_item={work_item}")
        do_workflow(mock_args)
        return

    elif subaction in ["start", "stop", "restart", "attach", "detach"]:
        print("Error: resident daemon subactions are deprecated in session-based runtime.", file=sys.stderr)
        sys.exit(1)

    elif subaction == "status":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            get_orchestrator_status)
        get_orchestrator_status(work_item)
        return

    elif subaction == "health":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            get_orchestrator_health)
        get_orchestrator_health(work_item)
        return

    elif subaction == "agents":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_agents_extended)
        print_agents_extended(work_item)
        return

    elif subaction == "tasks":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_tasks)
        print_tasks(work_item)
        return

    elif subaction == "queue":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_queue_extended)
        print_queue_extended(work_item)
        return

    elif subaction == "workflows":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_workflows_extended)
        print_workflows_extended(work_item)
        return

    elif subaction == "graph":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            render_graph_dag)
        render_graph_dag(work_item)
        return

    elif subaction == "locks":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_locks_extended)
        print_locks_extended(work_item)
        return

    elif subaction == "timeline":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_timeline_extended)
        print_timeline_extended(work_item)
        return

    elif subaction == "metrics":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_metrics_extended)
        print_metrics_extended(work_item)
        return

    elif subaction == "logs":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_logs_extended)
        print_logs_extended(
            work_item_id=work_item,
            level=getattr(args, "level", ""),
            agent=getattr(args, "agent", ""),
            workflow=getattr(args, "workflow", ""),
            work_item=getattr(args, "work_item", ""),
            orchestrator=getattr(args, "orchestrator", False),
            runtime=getattr(args, "runtime", False)
        )
        return

    elif subaction == "defects":
        from workflow_runtime.application.use_cases.orchestrator_status_presenter import (
            print_defects)
        print_defects(work_item)
        return

    elif subaction == "resume":
        obj_path = os.path.join(state_dir, "objective.json")
        obj = read_json_safe_local(obj_path)
        if obj:
            obj["status"] = "in_progress"
            write_json_atomic_local(obj_path, obj)
            log_event_local("run_resumed", "Run resumed via CLI.")
            print(json.dumps({"status": "success", "summary": "Run resumed."}))
        else:
            print(json.dumps({"status": "error", "summary": "No objective state found."}))
            sys.exit(1)

    elif subaction == "pause":
        obj_path = os.path.join(state_dir, "objective.json")
        obj = read_json_safe_local(obj_path)
        if obj:
            obj["status"] = "paused"
            write_json_atomic_local(obj_path, obj)
            log_event_local("run_paused", "Run paused via CLI.")
            print(json.dumps({"status": "success", "summary": "Run paused."}))
        else:
            print(json.dumps({"status": "error", "summary": "No objective state found."}))
            sys.exit(1)

    elif subaction == "cancel":
        obj_path = os.path.join(state_dir, "objective.json")
        obj = read_json_safe_local(obj_path)
        if obj:
            obj["status"] = "cancelled"
            write_json_atomic_local(obj_path, obj)
            log_event_local("run_cancelled", "Run cancelled via CLI.")
            print(json.dumps({"status": "success", "summary": "Run cancelled."}))
        else:
            print(json.dumps({"status": "error", "summary": "No objective state found."}))
            sys.exit(1)

    elif action == "cancel_task":
        if not task_id:
            print(json.dumps({"status": "error", "summary": "Missing task_id."}))
            sys.exit(1)
        tg_path = os.path.join(state_dir, "task_graph.json")
        tg = read_json_safe_local(tg_path)
        if tg and "tasks" in tg and task_id in tg["tasks"]:
            tg["tasks"][task_id]["status"] = "cancelled"
            write_json_atomic_local(tg_path, tg)
            log_event_local("task_cancelled", f"Task {task_id} cancelled.")
            print(json.dumps({"status": "success", "summary": f"Task {task_id} cancelled."}))
        else:
            print(json.dumps({"status": "error", "summary": f"Task {task_id} not found."}))
            sys.exit(1)

    elif action == "retry_task":
        if not task_id:
            print(json.dumps({"status": "error", "summary": "Missing task_id."}))
            sys.exit(1)
        tg_path = os.path.join(state_dir, "task_graph.json")
        tg = read_json_safe_local(tg_path)
        if tg and "tasks" in tg and task_id in tg["tasks"]:
            tg["tasks"][task_id]["status"] = "pending"
            write_json_atomic_local(tg_path, tg)
            log_event_local("task_retried", f"Task {task_id} reset to pending.")
            print(json.dumps({"status": "success", "summary": f"Task {task_id} retried."}))
        else:
            print(json.dumps({"status": "error", "summary": f"Task {task_id} not found."}))
            sys.exit(1)

    elif action == "release_lock":
        if not lock_id:
            print(json.dumps({"status": "error", "summary": "Missing lock_id."}))
            sys.exit(1)
        locks_path = os.path.join(state_dir, "locks.json")
        locks = read_json_safe_local(locks_path)
        if locks and lock_id in locks:
            owner = locks[lock_id].get("owner")
            del locks[lock_id]
            write_json_atomic_local(locks_path, locks)
            log_event_local("lock_released", f"Lock {lock_id} released from {owner}.")
            print(json.dumps({"status": "success", "summary": f"Lock {lock_id} released."}))
        else:
            write_json_atomic_local(locks_path, {})
            log_event_local("lock_force_released", f"Force released lock {lock_id}.")
            print(json.dumps({"status": "success", "summary": f"Lock {lock_id} force released."}))

    elif action == "checkpoint":
        if not task_id:
            print(json.dumps({"status": "error", "summary": "Missing checkpoint name/id."}))
            sys.exit(1)
        cp_dir = os.path.join(state_dir, "checkpoints")
        os.makedirs(cp_dir, exist_ok=True)
        cp_path = os.path.join(cp_dir, f"{task_id}.json")

        cp_data = {
            "created_at": datetime.now().astimezone().isoformat(),
            "objective": read_json_safe_local(os.path.join(state_dir, "objective.json")),
            "agents": read_json_safe_local(os.path.join(state_dir, "agents.json")),
            "task_graph": read_json_safe_local(os.path.join(state_dir, "task_graph.json")),
            "locks": read_json_safe_local(os.path.join(state_dir, "locks.json")),
            "defects": read_json_safe_local(os.path.join(state_dir, "defects.json"))
        }
        write_json_atomic_local(cp_path, cp_data)
        log_event_local("checkpoint_created", f"Checkpoint {task_id} created.")
        print(json.dumps({"status": "success", "summary": f"Checkpoint {task_id} saved."}))

    elif action == "restore":
        if not task_id:
            print(json.dumps({"status": "error", "summary": "Missing checkpoint name/id to restore."}))
            sys.exit(1)
        cp_path = os.path.join(state_dir, "checkpoints", f"{task_id}.json")
        if not os.path.exists(cp_path):
            print(json.dumps({"status": "error", "summary": f"Checkpoint {task_id} not found."}))
            sys.exit(1)

        cp_data = read_json_safe_local(cp_path)
        if cp_data:
            if "objective" in cp_data and cp_data["objective"]:
                write_json_atomic_local(os.path.join(state_dir, "objective.json"), cp_data["objective"])
            if "agents" in cp_data and cp_data["agents"]:
                write_json_atomic_local(os.path.join(state_dir, "agents.json"), cp_data["agents"])
            if "task_graph" in cp_data and cp_data["task_graph"]:
                write_json_atomic_local(os.path.join(state_dir, "task_graph.json"), cp_data["task_graph"])
            if "locks" in cp_data and cp_data["locks"]:
                write_json_atomic_local(os.path.join(state_dir, "locks.json"), cp_data["locks"])

            log_event_local("checkpoint_restored", f"State restored to checkpoint {task_id}.")
            print(json.dumps({"status": "success", "summary": f"Checkpoint {task_id} restored."}))
        else:
            print(json.dumps({"status": "error", "summary": "Failed to read checkpoint data."}))
            sys.exit(1)

    else:
        print(json.dumps({"status": "error", "summary": f"Unknown action: {action}"}))
        sys.exit(1)


__all__ = ["do_orchestrator"]
