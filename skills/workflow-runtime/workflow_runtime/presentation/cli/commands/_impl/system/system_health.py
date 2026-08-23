"""Handlers: do_api_server, do_validate, do_notify_action, do_doctor_action, do_debug_action, do_verify_action, do_release_action. Auto-extracted by QUICK-039 P3."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, cast

from workflow_runtime.infrastructure.persistence.checkpoint import (
    validate_checkpoint_level)
from workflow_runtime.infrastructure.session.session_io import (
    load_session, save_session_atomic)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    _run_core_cli_handler)
from workflow_runtime.presentation.cli.commands._impl.system.observatory_handler import (
    WorkflowObservatoryHTTPHandler)
from workflow_runtime.presentation.cli.workflow_runtime_shared import (
    update_context_health)


def do_api_server(args: argparse.Namespace) -> None:
    import http.server
    port = int(cast(int, getattr(args, "port", 31000) or 31000))
    host = str(getattr(args, "host", "localhost") or "localhost")
    server_address = (host, port)

    class HTTPServerV6(http.server.HTTPServer):
        allow_reuse_address = True

    httpd = HTTPServerV6(server_address, cast(Any, WorkflowObservatoryHTTPHandler))
    print(f"Workflow Observatory API Server running on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()


def do_validate(args: argparse.Namespace) -> int:
    sub = getattr(args, "subaction", None)
    if sub:
        act_val = getattr(args, 'action', None) or sub
        if act_val == "blueprint":
            from workflow_runtime.application.docs.artifact_validator import (
                validate_blueprint_file)
            res = validate_blueprint_file(str(getattr(args, "file", "")))
        elif act_val == "artifact":
            from workflow_runtime.application.docs.artifact_validator import (
                validate_artifact_general)
            res = validate_artifact_general(str(getattr(args, "file", "")))
        elif act_val == "session":
            session = load_session()
            if not session:
                res = {"status": "failure", "command": "validate session", "summary": "Session file not found."}
            else:
                from workflow_runtime.shared.drift import check_context_drift
                drifted, msg = check_context_drift(session)
                if drifted:
                    res = {"status": "failure", "command": "validate session", "summary": f"Session is unhealthy (drift detected: {msg})."}
                else:
                    res = {"status": "success", "command": "validate session", "summary": "Session is healthy."}
        else:
            res = {"status": "failure", "command": "validate", "summary": "Invalid validate subaction."}
        print(json.dumps(res, indent=2))
        if res.get("status") != "success":
            sys.exit(1)
        return 0

    session = load_session()
    if not session:
        print("Error: session file missing.", file=sys.stderr)
        sys.exit(1)

    update_context_health(session)
    if session.get("context_health") == "broken":
        print("Error: Context health is broken (drift detected).", file=sys.stderr)
        sys.exit(1)

    cp_val = getattr(args, "checkpoint", None)
    if cp_val:
        curr = int(cast(int, session.get("checkpoint", 1)))
        req_cp = str(cp_val)
        if not validate_checkpoint_level(curr, req_cp):
            print(f"Error: checkpoint validation failed (current={curr}, required={req_cp}).", file=sys.stderr)
            sys.exit(1)
    save_session_atomic(session)
    print("Validation passed.")
    return 0


def do_notify_action(args: argparse.Namespace) -> int:
    res = _run_core_cli_handler("handle_notify", args)
    return int(res) if res is not None else 0


def do_doctor_action(args: argparse.Namespace) -> int:
    res = _run_core_cli_handler("handle_doctor", args)
    return int(res) if res is not None else 0


def do_debug_action(args: argparse.Namespace) -> int:
    from workflow_runtime.application.verification.validation_runner import (
        run_debug)
    res_dict = run_debug()
    print(json.dumps(res_dict, indent=2))
    if res_dict.get("status") != "success":
        sys.exit(1)
    return 0


def do_verify_action(args: argparse.Namespace) -> int:
    if getattr(args, "subaction", None) is None:
        res = _run_core_cli_handler("handle_verify", args)
        return int(res) if res is not None else 0

    from workflow_runtime.application.verification.validation_runner import (
        run_verify)
    res_dict = run_verify()
    print(json.dumps(res_dict, indent=2))
    if res_dict.get("status") != "success":
        sys.exit(1)
    return 0


def do_release_action(args: argparse.Namespace) -> int:
    action = str(getattr(args, 'action', None) or getattr(args, 'subaction', None) or "status")
    version = str(getattr(args, "version", None) or "0.0.0")
    dry_run = bool(getattr(args, "dry_run", False))
    approve_val = bool(getattr(args, "approve", False))

    res: dict[str, Any]
    if action == "plan":
        from workflow_runtime.application.workflow.release_manager import (
            run_release_plan)
        res = run_release_plan()
    elif action == "execute":
        from workflow_runtime.application.workflow.release_manager import (
            run_release_execute)
        res = run_release_execute(approve=approve_val)
    elif action == "validate":
        from workflow_runtime.application.release.release_gate_service import (
            ReleaseGateService)
        gate = ReleaseGateService(".")
        result = gate.evaluate()
        res = {
            "status": "success" if result.passed or dry_run else "failure",
            "action": "validate",
            "dry_run": dry_run,
            "score": result.score,
            "details": result.details,
        }
        if dry_run and result.errors:
            res["warnings"] = result.errors
        else:
            res["errors"] = result.errors
    elif action in {"status", "tag", "publish", "rollback"}:
        res = {
            "status": "success",
            "action": action,
            "version": version,
            "dry_run": dry_run,
            "summary": (
                f"Release {action} dry-run completed."
                if dry_run else f"Release {action} command accepted."
            ),
        }
    else:
        res = {"status": "failure", "summary": "Invalid release subaction."}

    print(json.dumps(res, indent=2))
    return 0 if res.get("status") == "success" else 1


def do_post_release_action(args: argparse.Namespace) -> int:
    action = str(getattr(args, "action", None) or "run")
    version = str(getattr(args, "version", None) or "0.0.0")
    commit = str(getattr(args, "commit", None) or "HEAD")
    output_dir = str(getattr(args, "output_dir", None) or "docs/verification")
    res: dict[str, Any]
    if action == "status":
        res = {
            "status": "success",
            "action": "status",
            "output_dir": output_dir,
            "summary": "Post-release lifecycle command is available.",
        }
    elif action == "run":
        from workflow_runtime.application.workflow.post_release_lifecycle import (
            PostReleaseLifecycleAutomator)
        reports = PostReleaseLifecycleAutomator(
            release_version=version,
            git_commit=commit,
            output_dir=output_dir,
        ).run_all_phases()
        res = {
            "status": "success",
            "action": "run",
            "version": version,
            "commit": commit,
            "reports": reports,
        }
    else:
        res = {"status": "failure", "summary": "Invalid post-release action."}

    print(json.dumps(res, indent=2))
    return 0 if res.get("status") == "success" else 1


__all__ = [
    "do_api_server",
    "do_validate",
    "do_notify_action",
    "do_doctor_action",
    "do_debug_action",
    "do_verify_action",
    "do_release_action",
    "do_post_release_action",
]
