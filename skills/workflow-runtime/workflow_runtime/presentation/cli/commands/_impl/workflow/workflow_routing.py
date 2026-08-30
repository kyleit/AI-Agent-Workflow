from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.infrastructure.session.session_io import load_session
from workflow_runtime.application.command_contract import (
    CommandResult,
    NextAction,
    emit_result,
)


def _normalize_active_workflow(active_flow: Any, session: dict[str, Any]) -> dict[str, Any] | None:
    if not active_flow:
        return None
    if isinstance(active_flow, str):
        wf_id = active_flow
        phase = str(session.get("active_phase") or session.get("current_step") or "unknown")
        next_step = str(session.get("suggested_next_skill") or session.get("current_skill") or "unknown")
        return {
            "workflow_id": wf_id,
            "current_phase": phase,
            "next_step": next_step,
            "status": str(session.get("status") or "in_progress"),
            "checkpoint": session.get("checkpoint", 1),
        }
    if isinstance(active_flow, dict):
        wf_dict = cast(dict[str, Any], active_flow)
        wf_id = str(wf_dict.get("workflow_id") or wf_dict.get("type") or wf_dict.get("id") or "unknown")
        phase = str(wf_dict.get("current_phase") or wf_dict.get("phase") or wf_dict.get("active_phase") or "unknown")
        next_step = str(wf_dict.get("next_step") or wf_dict.get("suggested_next_skill") or wf_dict.get("command") or "unknown")
        status = str(wf_dict.get("status") or session.get("status") or "in_progress")
        checkpoint = wf_dict.get("checkpoint") or session.get("checkpoint", 1)
        return {
            "workflow_id": wf_id,
            "current_phase": phase,
            "next_step": next_step,
            "status": status,
            "checkpoint": checkpoint,
        }
    return None


def do_workflow(args: argparse.Namespace) -> int:
    subaction = getattr(args, "action", None) or getattr(args, "subaction", None)

    if subaction == "trace":
        from workflow_runtime.infrastructure.events.event_logger import get_logger
        logger = get_logger()
        read_fn: Any = getattr(logger, "read_all", None)
        events: list[dict[str, Any]] = cast(list[dict[str, Any]], read_fn()) if callable(read_fn) else []

        target_req_id: str | None = cast(str | None, getattr(args, "request_id", None))

        if not target_req_id:
            received_events = [e for e in events if e.get("event_type") == "workflow.request.received"]
            if received_events:
                p_dict = cast(dict[str, Any], received_events[-1].get("payload", {}))
                target_req_id = str(p_dict.get("request_id", ""))

        if not target_req_id:
            print("No active workflow request found.", file=sys.stderr)
            sys.exit(1)

        req_events: list[dict[str, Any]] = []
        for e in events:
            payload = cast(dict[str, Any], e.get("payload", {}))
            if payload.get("request_id") == target_req_id:
                req_events.append(e)

        if not req_events:
            print(f"Request ID '{target_req_id}' not found.", file=sys.stderr)
            sys.exit(1)

        intent = "unknown"
        workflow_id = "unknown"
        current_phase = "unknown"
        skill = "unknown"
        status = "RUNNING"

        for e in req_events:
            etype = str(e.get("event_type", ""))
            payload = cast(dict[str, Any], e.get("payload", {}))

            if etype == "workflow.request.received":
                intent = str(payload.get("intent", "unknown"))
            elif etype == "workflow.started":
                workflow_id = str(payload.get("workflow_id", "unknown"))
            elif etype == "workflow.phase.started":
                current_phase = str(payload.get("phase", "unknown"))
            elif etype in ("skill.selected", "skill.started"):
                skill = str(payload.get("skill", "unknown"))
            elif etype == "workflow.completed":
                status = "COMPLETED"

        print(str(target_req_id))
        print()
        print("Intent:")
        if intent == "engineering":
            print("feature_request")
        else:
            print(intent)
        print()
        print("Workflow:")
        if workflow_id != "unknown":
            print("feature-development")
        else:
            print("unknown")
        print()
        print("Current:")
        print(current_phase)
        print()
        print("Skill:")
        print(skill)
        print()
        print("Status:")
        print(status)
        return 0

    elif subaction == "submit":
        from workflow_runtime.application.workflow.workflow_entry_gateway import WorkflowEntryGateway
        gateway = WorkflowEntryGateway(".")
        prompt = str(getattr(args, "prompt", ""))
        previous_json_output = os.environ.get("AIWF_JSON_OUTPUT")
        os.environ["AIWF_JSON_OUTPUT"] = "1"
        try:
            handle_fn: Any = getattr(gateway, "handle_request", None)
            res: dict[str, Any] = cast(dict[str, Any], handle_fn(prompt)) if callable(handle_fn) else {}
        finally:
            if previous_json_output is None:
                os.environ.pop("AIWF_JSON_OUTPUT", None)
            else:
                os.environ["AIWF_JSON_OUTPUT"] = previous_json_output
        if res.get("status") == "ROUTED":
            next_skill = str(res.get("next_skill") or "")
            next_command = str(res.get("next_command") or res.get("suggested_next_command") or "")
            result = CommandResult(
                command="workflow submit",
                status="success",
                summary="Workflow request accepted and routed.",
                data=res,
                side_effects=(".agents/state",),
                next_action=NextAction(
                    skill=next_skill or None,
                    command=next_command or None,
                    automatic=True,
                ),
                request_id=str(res.get("request_id") or ""),
            )
            return emit_result(result, sys.stdout)
        print(json.dumps(res, indent=2))
        return 0

    elif subaction == "resume":
        session = load_session() or {}
        active_flow = session.get("active_workflow")
        if not active_flow and os.path.exists(".agents/state/active_workflow.json"):
            try:
                with open(".agents/state/active_workflow.json", "r", encoding="utf-8") as f:
                    active_flow = json.load(f)
            except Exception:
                pass

        normalized = _normalize_active_workflow(active_flow, session)
        if not normalized:
            print("Error: No active workflow to resume.", file=sys.stderr)
            return 1

        wf_id = normalized["workflow_id"]
        phase = normalized["current_phase"]
        next_step = normalized["next_step"]

        print(f"Resuming workflow '{wf_id}' at phase '{phase}'")
        print(f"Next recommended action: {next_step}")
        return 0

    elif subaction == "status":
        session = load_session() or {}
        active_flow = session.get("active_workflow")
        if not active_flow and os.path.exists(".agents/state/active_workflow.json"):
            try:
                with open(".agents/state/active_workflow.json", "r", encoding="utf-8") as f:
                    active_flow = json.load(f)
            except Exception:
                pass

        normalized = _normalize_active_workflow(active_flow, session)
        if not normalized:
            print("No active workflow running.")
            return 0

        print(json.dumps(normalized, indent=2))
        return 0

    elif subaction == "list-events":
        from workflow_runtime.infrastructure.events.event_logger import get_logger
        logger = get_logger()
        read_fn: Any = getattr(logger, "read_all", None)
        events: list[dict[str, Any]] = cast(list[dict[str, Any]], read_fn()) if callable(read_fn) else []
        target_req_id = getattr(args, "request_id", None)
        if target_req_id:
            events = [e for e in events if cast(dict[str, Any], e.get("payload", {})).get("request_id") == target_req_id]
        print(json.dumps(events, indent=2))
        return 0

    else:
        print(f"Unknown workflow action: {subaction}", file=sys.stderr)
        return 1


def do_active_workflow(args: argparse.Namespace) -> int:
    session = load_session() or {}
    active_flow = session.get("active_workflow")
    if not active_flow and os.path.exists(".agents/state/active_workflow.json"):
        try:
            with open(".agents/state/active_workflow.json", "r", encoding="utf-8") as f:
                active_flow = json.load(f)
        except Exception:
            pass

    normalized = _normalize_active_workflow(active_flow, session)
    as_json = bool(getattr(args, "json", False))

    if not normalized:
        if as_json:
            print(json.dumps({
                "active": False,
                "workflow_id": None,
                "current_phase": None,
                "next_step": None,
            }, indent=2))
        else:
            print("No active workflow.")
        return 0

    if as_json:
        payload = {
            "active": True,
            **normalized,
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Workflow ID: {normalized['workflow_id']}")
        print(f"Current Phase: {normalized['current_phase']}")
        print(f"Next Step: {normalized['next_step']}")
    return 0


def do_routing(args: argparse.Namespace) -> int:
    prompt = str(getattr(args, "prompt", "") or "")
    from workflow_runtime.application.workflow.workflow_entry_gateway import WorkflowEntryGateway
    gateway = WorkflowEntryGateway(".")
    handle_fn: Any = getattr(gateway, "handle_request", None)
    res: dict[str, Any] = cast(dict[str, Any], handle_fn(prompt)) if callable(handle_fn) else {}
    print(json.dumps(res, indent=2))
    return 0


def do_discover_action(args: argparse.Namespace) -> int:
    target_dir = str(getattr(args, "path", ".") or ".")
    from workflow_runtime.application.workflow.workflow_entry_gateway import WorkflowEntryGateway
    gateway = WorkflowEntryGateway(target_dir)
    disc_fn: Any = getattr(gateway, "discover_project_profile", None)
    profile: dict[str, Any] = cast(dict[str, Any], disc_fn()) if callable(disc_fn) else {}
    print(json.dumps(profile, indent=2))
    return 0


def do_classify_action(args: argparse.Namespace) -> int:
    prompt = str(getattr(args, "prompt", "") or "")
    from workflow_runtime.application.workflow.workflow_entry_gateway import WorkflowEntryGateway
    gateway = WorkflowEntryGateway(".")
    classifier = getattr(gateway, "classifier", None)
    classify_fn: Any = getattr(classifier, "classify_intent", None) if classifier else None
    intent = classify_fn(prompt) if callable(classify_fn) else "engineering"
    print(json.dumps({"prompt": prompt, "classified_intent": intent}, indent=2))
    return 0


def do_coordinator_action(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.knowledge_command_handlers import handle_coordinator
    return handle_coordinator(args)


def do_dispatch_action(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.workflow_command_handlers import handle_dispatch
    return handle_dispatch(args)


__all__ = [
    "do_workflow",
    "do_active_workflow",
    "do_routing",
    "do_discover_action",
    "do_classify_action",
    "do_coordinator_action",
    "do_dispatch_action",
]
