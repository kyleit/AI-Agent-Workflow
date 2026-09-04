"""
workflow_runtime/presentation/cli/workflow_command_handlers.py

CLI command handlers for AIWF workflow coordination, dispatch, execution, blueprints, and suggestions.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, cast


def handle_dispatch(args: argparse.Namespace) -> int:
    lane_fields = ["project_id", "workflow_id", "agent_id", "task_id"]
    lane_values = {field: str(getattr(args, field, "") or "") for field in lane_fields}
    has_lane = any(lane_values.values()) or bool(getattr(args, "approval_file", None))
    lane_scheduler: Any = None
    lane_key: Any = None
    if has_lane:
        from workflow_runtime.application.workflow.lane_scheduler import (
            ExecutionLane, LaneScheduler)
        from workflow_runtime.domain.approval import ApprovalRecord, LaneKey

        missing = [field for field, value in lane_values.items() if not value]
        artifact_sha = str(getattr(args, "artifact_sha256", "") or "")
        approval_file = str(getattr(args, "approval_file", "") or "")
        if missing or not artifact_sha or not approval_file:
            print(json.dumps({
                "status": "invalid_input",
                "blocking_findings": ["lane_identity_or_approval_missing"],
                "missing": missing + (["artifact_sha256"] if not artifact_sha else []) + (["approval_file"] if not approval_file else []),
                "next_action": "provide complete lane metadata and approval file",
            }, indent=2))
            return 2
        try:
            with open(approval_file, "r", encoding="utf-8") as handle:
                raw_approval = json.load(handle)
            if isinstance(raw_approval, dict) and isinstance(raw_approval.get("approval"), dict):
                raw_approval = raw_approval["approval"]
            approval = ApprovalRecord.from_dict(cast(dict[str, Any], raw_approval))
            lane_key = LaneKey(**lane_values)
            lane_scheduler = LaneScheduler()
            decision = lane_scheduler.schedule_lanes([
                ExecutionLane.create(
                    lane_key,
                    getattr(args, "write_set", []) or [],
                    approval,
                    artifact_sha,
                )
            ])
            if decision.blocked:
                print(json.dumps(decision.to_dict(), indent=2))
                return 2
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(json.dumps({
                "status": "invalid_input",
                "blocking_findings": ["lane_approval_invalid"],
                "error": str(exc),
            }, indent=2))
            return 2

    from workflow_runtime.application.agent.dispatch_service import (
        AgentDispatchService)
    service = AgentDispatchService()
    role_val = str(getattr(args, "agent", None) or getattr(args, "role", None) or "")
    task_val = str(getattr(args, "task", ""))
    model_val = getattr(args, "model", None)
    dry_val = bool(getattr(args, "dry_run", False))
    res = service.dispatch_agent(
        role=role_val,
        task=task_val,
        model=str(model_val) if model_val else None,
        dry_run=dry_val,
    )
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    if lane_scheduler is not None and lane_key is not None:
        lane_scheduler.release(lane_key)
    return 0 if res.status == "SUCCESS" else 1


def handle_coordinator(args: argparse.Namespace) -> int:
    from workflow_runtime.application.workflow.coordinator_service import (
        WorkflowCoordinatorService)
    from workflow_runtime.application.workflow.gate_service import (
        ApprovalGateService)
    from workflow_runtime.application.workflow.phase_service import (
        PhaseTransitionService)
    from workflow_runtime.infrastructure.persistence.state_store import (
        StateStoreAdapter)
    repo = StateStoreAdapter()
    phase_svc = PhaseTransitionService(repo)
    gate_svc = ApprovalGateService()
    coordinator = WorkflowCoordinatorService(repo, phase_svc, gate_svc)
    dry_val = bool(getattr(args, "dry_run", False))
    res = coordinator.tick(dry_run=dry_val)
    print(f"TICK SUCCESS: session={res.session_id} phase={res.active_phase} status={res.status}")
    return 0


def handle_workflow(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing import (
        do_workflow)
    return do_workflow(args)


def handle_execution(args: argparse.Namespace) -> int:
    from workflow_runtime.application.use_cases.execution_manager import (
        ExecutionManager, ProcessRegistry)

    sub = getattr(args, "subcommand", None)

    if sub == "list":
        data = ProcessRegistry.read()
        if not data:
            print("No executions found.")
        else:
            for eid, info_raw in data.items():
                if isinstance(info_raw, dict):
                    info = cast(dict[str, Any], info_raw)
                    raw_cmd = info.get("command", "")
                    print(f"  [{eid}] status={info.get('status')} cmd={str(raw_cmd)[:60]}")
        return 0

    elif sub == "cancel":
        id_val = getattr(args, "id", None)
        if not id_val:
            print("--id required for cancel", file=sys.stderr)
            return 2
        reason_val = str(getattr(args, "reason", None) or "CLI cancel")
        ExecutionManager.cancel(str(id_val), reason_val)
        print(f"Cancelled: {id_val}")
        return 0

    elif sub == "kill":
        id_val = getattr(args, "id", None)
        if not id_val:
            print("--id required for kill", file=sys.stderr)
            return 2
        reason_val = str(getattr(args, "reason", None) or "CLI kill")
        ExecutionManager.kill(str(id_val), reason_val)
        print(f"Killed: {id_val}")
        return 0

    elif sub == "recover":
        recovered = ExecutionManager.recover()
        print(f"Recovered {recovered} execution(s).")
        return 0

    elif sub == "capacity":
        cpus, total, avail = ExecutionManager.get_system_capacity()
        print(f"Capacity: CPUs={cpus} total={total} available={avail}")
        return 0

    return 0


def handle_blueprint(args: argparse.Namespace) -> int:
    """Register or approve a Technical Design Blueprint for a work item."""
    from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
        do_blueprint)
    return do_blueprint(args)


def handle_suggest(args: argparse.Namespace) -> int:
    """Suggest a workflow skill based on request classification."""
    from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
        do_suggest)
    return do_suggest(args)


def handle_start(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
        do_task)
    do_task(args)
    return 0


def handle_step(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
        do_task)
    do_task(args)
    return 0


def handle_complete(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
        do_task)
    do_task(args)
    return 0


def handle_fail(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.workflow.task_manager import (
        do_task)
    do_task(args)
    return 0


def handle_validate(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing import (
        do_workflow)
    return do_workflow(args)


def handle_verify(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.commands._impl.workflow.workflow_routing import (
        do_workflow)
    return do_workflow(args)


__all__ = [
    "handle_dispatch",
    "handle_workflow",
    "handle_blueprint",
    "handle_suggest",
    "handle_start",
    "handle_step",
    "handle_complete",
    "handle_fail",
    "handle_validate",
    "handle_verify",
]
