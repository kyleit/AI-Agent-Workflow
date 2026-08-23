from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def do_implement_action(args: Any) -> None:
    subaction = str(getattr(args, "subaction", "status"))
    if subaction == "status":
        try:
            from workflow_runtime.application.verification.release_gate import (
                ReleaseGate)
            allowed, reason = ReleaseGate(os.getcwd()).validate()
        except Exception as e:
            allowed, reason = False, str(e)
        print(json.dumps({"status": "ok", "current_phase": None, "phases": [], "release_allowed": bool(allowed), "release_block_reason": "" if allowed else reason}, indent=2))
        return
    if subaction == "resume":
        print(json.dumps({"status": "nothing_to_resume", "message": "No pending implementation phase found."}, indent=2))
        sys.exit(1)
    if subaction == "abort":
        print(json.dumps({"status": "aborted", "workers_killed": 0, "locks_released": 0}, indent=2))
        return


def do_project_version_cached(args: argparse.Namespace) -> None:
    """Read project version from cached context.json only — never scans manifests."""
    from workflow_runtime.shared.version_detector import (
        detect_project_version_cached)
    subaction = str(getattr(args, 'action', None) or getattr(args, 'subaction', None))
    if subaction == "version":
        info_dict = detect_project_version_cached()
        print(json.dumps(info_dict, indent=2))
        if str(info_dict.get("version", "0.0.0")) == "0.0.0":
            sys.exit(1)
    else:
        print(f"Unknown project subaction: {subaction}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "do_implement_action",
    "do_project_version_cached",
]
