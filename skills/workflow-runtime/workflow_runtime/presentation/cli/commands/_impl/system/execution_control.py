from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, cast

from workflow_runtime.infrastructure.session.session_io import (
    load_session, save_session_atomic)


def do_execution(args: argparse.Namespace) -> None:
    plan_file = os.path.join(".agents", "runtime", "execution-plan.json")
    os.makedirs(os.path.dirname(plan_file), exist_ok=True)

    plan: dict[str, Any] = {}
    if os.path.exists(plan_file):
        try:
            with open(plan_file, "r", encoding="utf-8") as f:
                raw_plan = json.load(f)
                if isinstance(raw_plan, dict):
                    plan = cast(dict[str, Any], raw_plan)
        except Exception:
            pass

    session = load_session()
    _ = session.get("checkpoint", 1)

    sub_act = str(getattr(args, 'action', None) or getattr(args, 'subaction', None) or "")

    if sub_act == "recommend":
        mode_arg = getattr(args, "mode", None)
        reason_arg = getattr(args, "reason", None)
        if not mode_arg or not reason_arg:
            print("Error: --mode and --reason are required.", file=sys.stderr)
            sys.exit(1)
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

    elif sub_act == "mode":
        mode_arg = getattr(args, "mode", None)
        if not mode_arg:
            print("Error: --mode is required.", file=sys.stderr)
            sys.exit(1)
        if mode_arg == "parallel":
            print("Error: Parallel execution mode is disabled. Only sequential execution is supported.", file=sys.stderr)
            sys.exit(1)

        plan["implementation_execution_mode"] = mode_arg
        plan["execution_mode"] = mode_arg
        if getattr(args, "approve", False):
            plan["approved"] = True
        with open(plan_file, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        print(f"Execution mode updated to {mode_arg} (Approved: {plan.get('approved')}).")

    elif sub_act == "summary":
        summary_text = """================================================================================

Execution Plan Summary

This framework operates in a strict Sequential Workflow Engine mode.
No parallel worker pools or concurrent executions are allowed to prevent
state drift and write contamination.

================================================================================
"""
        print(summary_text)

    else:
        from workflow_runtime.application.use_cases.execution_manager import (
            ExecutionManager, ProcessRegistry)
        ExecutionManager.start_scheduler()

        if sub_act == "submit":
            cmd_arg = getattr(args, "command", None)
            if not cmd_arg:
                print("Error: --command is required for submit.", file=sys.stderr)
                sys.exit(1)
            req: dict[str, Any] = {
                "task_id": getattr(args, "task_id", None) or "TASK-N/A",
                "owner_agent_id": getattr(args, "owner_agent", None) or "AGENT-UNKNOWN",
                "command": cmd_arg,
                "arguments": getattr(args, "arguments", None) or [],
                "working_directory": getattr(args, "cwd", None) or ".",
                "timeout": getattr(args, "timeout", None),
                "stdin_mode": getattr(args, "stdin_mode", None) or "disabled",
                "priority": getattr(args, "priority", None) or "normal",
                "is_force_task": getattr(args, "is_force_task", None) or False,
                "cpu_limit": getattr(args, "cpu_limit", None) or 1.0,
                "memory_limit": getattr(args, "memory_limit", None) or 0.5
            }
            try:
                exec_id = ExecutionManager.submit(req)
                print(f"Submitted execution: {exec_id}")
                ExecutionManager.tick_scheduler()
            except Exception as e:
                print(f"Error submitting execution: {e}", file=sys.stderr)
                sys.exit(1)

        elif sub_act == "list":
            data = ProcessRegistry.read()
            print(f"{'EXECUTION ID':<18} | {'TASK ID':<10} | {'OWNER AGENT':<15} | {'PID':<6} | {'STATUS':<15} | {'COMMAND':<30}")
            print("-" * 105)
            for _k, v_raw in data.items():
                if isinstance(v_raw, dict):
                    v = cast(dict[str, Any], v_raw)
                    raw_args = v.get("arguments", [])
                    args_list = cast(list[Any], raw_args) if isinstance(raw_args, list) else []
                    cmd_sum = " ".join([str(v.get("command", ""))] + [str(a) for a in args_list])[:30]
                    print(f"{str(v.get('execution_id', '')):<18} | {str(v.get('task_id', 'N/A')):<10} | {str(v.get('owner_agent_id', 'N/A')):<15} | {str(v.get('pid') or ''):<6} | {str(v.get('status', '')):<15} | {cmd_sum:<30}")

        elif sub_act == "read":
            id_arg = getattr(args, "id", None)
            if not id_arg:
                print("Error: --id is required for read.", file=sys.stderr)
                sys.exit(1)
            data = ProcessRegistry.read()
            item = data.get(id_arg)
            if not item:
                print(f"Execution not found: {id_arg}", file=sys.stderr)
                sys.exit(1)
            print(json.dumps(item, indent=2))

        elif sub_act == "stream":
            id_arg = getattr(args, "id", None)
            if not id_arg:
                print("Error: --id is required for stream.", file=sys.stderr)
                sys.exit(1)
            data = ProcessRegistry.read()
            raw_item = data.get(id_arg)
            if not raw_item or not isinstance(raw_item, dict):
                print(f"Execution not found: {id_arg}", file=sys.stderr)
                sys.exit(1)
            item = cast(dict[str, Any], raw_item)

            stdout_path = str(item.get("stdout_artifact", ""))
            stderr_path = str(item.get("stderr_artifact", ""))
            print(f"Streaming logs for {id_arg} (Ctrl+C to stop)...")
            try:
                out_pos = 0
                err_pos = 0
                while True:
                    cur_data = ProcessRegistry.read()
                    raw_cur_item = cur_data.get(id_arg)
                    if not raw_cur_item or not isinstance(raw_cur_item, dict):
                        break
                    item_current = cast(dict[str, Any], raw_cur_item)

                    if os.path.exists(stdout_path):
                        with open(stdout_path, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(out_pos)
                            chunk = f.read()
                            if chunk:
                                sys.stdout.write(chunk)
                                sys.stdout.flush()
                            out_pos = f.tell()

                    if os.path.exists(stderr_path):
                        with open(stderr_path, "r", encoding="utf-8", errors="ignore") as f:
                            f.seek(err_pos)
                            chunk = f.read()
                            if chunk:
                                sys.stderr.write(chunk)
                                sys.stderr.flush()
                            err_pos = f.tell()

                    st = str(item_current.get("status", ""))
                    if st in ["COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT", "ORPHANED", "BLOCKED_INTERACTIVE"]:
                        break
                    time.sleep(0.2)
            except KeyboardInterrupt:
                print("\nStopped streaming logs.")

        elif sub_act == "cancel":
            id_arg = getattr(args, "id", None)
            if not id_arg:
                print("Error: --id is required for cancel.", file=sys.stderr)
                sys.exit(1)
            reason = str(getattr(args, "reason", None) or "Cancelled by user via CLI")
            ExecutionManager.cancel(id_arg, reason)
            print(f"Cancellation requested for {id_arg}.")

        elif sub_act == "kill":
            id_arg = getattr(args, "id", None)
            if not id_arg:
                print("Error: --id is required for kill.", file=sys.stderr)
                sys.exit(1)
            reason = str(getattr(args, "reason", None) or "Killed by user via CLI")
            ExecutionManager.kill(id_arg, reason)
            print(f"Force killed {id_arg}.")

        elif sub_act == "pause":
            id_arg = getattr(args, "id", None)
            if not id_arg:
                print("Error: --id is required for pause.", file=sys.stderr)
                sys.exit(1)
            try:
                ExecutionManager.pause(id_arg)
                print(f"Paused execution {id_arg}.")
            except Exception as e:
                print(f"Error pausing: {e}", file=sys.stderr)
                sys.exit(1)

        elif sub_act == "resume":
            id_arg = getattr(args, "id", None)
            if not id_arg:
                print("Error: --id is required for resume.", file=sys.stderr)
                sys.exit(1)
            try:
                ExecutionManager.resume(id_arg)
                print(f"Resumed execution {id_arg}.")
            except Exception as e:
                print(f"Error resuming: {e}", file=sys.stderr)
                sys.exit(1)

        elif sub_act == "recover":
            recovered = ExecutionManager.recover()
            print(f"Orphan recovery completed. Recovered/reattached executions: {recovered}")

        elif sub_act == "capacity":
            cpu, total, avail = ExecutionManager.get_system_capacity()
            print("System Capacity Profile:")
            print(f"- Logical CPUs: {cpu}")
            print(f"- Total Memory: {total / (1024**3):.2f} GB")
            print(f"- Available Memory: {avail / (1024**3):.2f} GB")


def sync_analysis_agents_to_session() -> None:
    session = load_session()
    analysis_file = os.path.join(".agents", "runtime", "analysis-agents.json")
    if os.path.exists(analysis_file):
        try:
            with open(analysis_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data_dict = cast(dict[str, Any], data)
                    session["analysis_agents"] = data_dict.get("agents", [])
                else:
                    session["analysis_agents"] = []
        except Exception:
            session["analysis_agents"] = []
    else:
        session["analysis_agents"] = []
    save_session_atomic(session)


__all__ = [
    "do_execution",
    "sync_analysis_agents_to_session",
]
