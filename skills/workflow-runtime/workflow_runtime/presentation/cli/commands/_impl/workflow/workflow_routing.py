from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, cast

from workflow_runtime.infrastructure.session.session_io import load_session


def do_workflow(args: argparse.Namespace) -> int:
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)

    if subaction == "trace":
        from workflow_runtime.infrastructure.events.event_logger import             get_logger
        logger = get_logger()
        read_fn: Any = getattr(logger, "read_all", None)
        events: list[dict[str, Any]] = cast(list[dict[str, Any]], read_fn()) if callable(read_fn) else []

        target_req_id: str | None = cast(str | None, getattr(args, "request_id", None))

        # If request-id is not provided, find the latest request received event
        if not target_req_id:
            received_events = [e for e in events if e.get("event_type") == "workflow.request.received"]
            if received_events:
                p_dict = cast(dict[str, Any], received_events[-1].get("payload", {}))
                target_req_id = str(p_dict.get("request_id", ""))

        if not target_req_id:
            print("No active workflow request found.", file=sys.stderr)
            sys.exit(1)

        # Filter all events related to this request_id
        req_events: list[dict[str, Any]] = []
        for e in events:
            payload = cast(dict[str, Any], e.get("payload", {}))
            if payload.get("request_id") == target_req_id:
                req_events.append(e)

        if not req_events:
            print(f"Request ID '{target_req_id}' not found.", file=sys.stderr)
            sys.exit(1)

        # Parse intent, workflow, current, skill, status
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
        from workflow_runtime.application.workflow.workflow_entry_gateway import             WorkflowEntryGateway
        gateway = WorkflowEntryGateway(".")
        prompt = str(getattr(args, "prompt", ""))
        handle_fn: Any = getattr(gateway, "handle_request", None)
        res: dict[str, Any] = cast(dict[str, Any], handle_fn(prompt)) if callable(handle_fn) else {}

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

        if not active_flow:
            print("Error: No active workflow to resume.", file=sys.stderr)
            return 1

        wf_dict = cast(dict[str, Any], active_flow)
        wf_id = str(wf_dict.get("workflow_id", "unknown"))
        phase = str(wf_dict.get("current_phase", "unknown"))
        next_step = str(wf_dict.get("next_step", "unknown"))

        print(f"Resuming workflow '{wf_id}' at phase '{phase}'...")
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

        if not active_flow:
            print("No active workflow running.")
            return 0

        wf_dict = cast(dict[str, Any], active_flow)
        print(json.dumps(wf_dict, indent=2))
        return 0

    elif subaction == "list-events":
        from workflow_runtime.infrastructure.events.event_logger import             get_logger
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

    if not active_flow:
        print("No active workflow.")
        return 0

    wf_dict = cast(dict[str, Any], active_flow)
    print(f"Workflow ID: {wf_dict.get('workflow_id')}")
    print(f"Current Phase: {wf_dict.get('current_phase')}")
    print(f"Next Step: {wf_dict.get('next_step')}")
    return 0


def do_routing(args: argparse.Namespace) -> int:
    prompt = str(getattr(args, 'prompt', '') or '')
    from workflow_runtime.application.workflow.workflow_entry_gateway import \
        WorkflowEntryGateway
    gateway = WorkflowEntryGateway(".")
    handle_fn: Any = getattr(gateway, "handle_request", None)
    res: dict[str, Any] = cast(dict[str, Any], handle_fn(prompt)) if callable(handle_fn) else {}
    print(json.dumps(res, indent=2))
    return 0


def do_discover_action(args: argparse.Namespace) -> int:
    target_dir = str(getattr(args, 'path', '.') or '.')
    from workflow_runtime.application.workflow.workflow_entry_gateway import \
        WorkflowEntryGateway
    gateway = WorkflowEntryGateway(target_dir)
    disc_fn: Any = getattr(gateway, "discover_project_profile", None)
    profile: dict[str, Any] = cast(dict[str, Any], disc_fn()) if callable(disc_fn) else {}
    print(json.dumps(profile, indent=2))
    return 0


def do_classify_action(args: argparse.Namespace) -> int:
    prompt = str(getattr(args, 'prompt', '') or '')
    from workflow_runtime.application.workflow.workflow_entry_gateway import         WorkflowEntryGateway
    gateway = WorkflowEntryGateway(".")
    classifier = getattr(gateway, "classifier", None)
    classify_fn: Any = getattr(classifier, "classify_intent", None) if classifier else None
    intent = classify_fn(prompt) if callable(classify_fn) else "engineering"
    print(json.dumps({"prompt": prompt, "classified_intent": intent}, indent=2))
    return 0


def do_coordinator_action(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.knowledge_command_handlers import (
        handle_coordinator)
    return handle_coordinator(args)


def do_dispatch_action(args: argparse.Namespace) -> int:
    from workflow_runtime.presentation.cli.workflow_command_handlers import (
        handle_dispatch)
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
