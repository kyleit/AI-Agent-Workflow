from __future__ import annotations

import argparse
import os
import sys
from typing import Any, cast


def do_update(args: argparse.Namespace) -> int:
    from workflow_runtime.application.workflow import aiwf_registry
    from workflow_runtime.application.command_contract import (
        CommandResult,
        NextAction,
        emit_result,
    )

    update_all = bool(getattr(args, "all", False)) or getattr(args, "action", None) == "all"
    update_current = bool(getattr(args, "current", False))
    as_json = bool(getattr(args, "json", False))

    if not update_all and not update_current:
        if sys.stdout.isatty():
            print("Update mode:")
            print("1. Current project only")
            print("2. All registered projects")
            print("3. Cancel")
            try:
                choice = input("Enter choice (1-3): ").strip()
                if choice == "1":
                    update_current = True
                elif choice == "2":
                    update_all = True
                else:
                    print("Cancelled.")
                    return 0
            except (KeyboardInterrupt, EOFError):
                print("\nCancelled.")
                return 0
        else:
            update_current = True

    if update_all:
        summary = aiwf_registry.update_all_projects()
        failed_count = int(cast(int, summary.get("failed", 0)))
        if as_json:
            result = CommandResult(
                command="update",
                status="failure" if failed_count > 0 else "success",
                summary="AIWF project update batch completed.",
                data=summary,
                side_effects=("registered project installations",),
                next_action=NextAction(command="doctor"),
            )
            return emit_result(result, sys.stdout)

        print("Starting batch update of all registered projects...")
        print("\n==================================================")
        print("AIWF Update Summary:")
        print(f"  Total registered: {summary.get('total', 0)}")
        print(f"  Updated:          {summary.get('updated', 0)}")
        print(f"  Skipped:          {summary.get('skipped', 0)}")
        print(f"  Failed:           {summary.get('failed', 0)}")
        print(f"  Missing:          {summary.get('missing', 0)}")
        print("==================================================")
        if failed_count > 0:
            print("\nFailed updates:")
            raw_details = summary.get("details")
            details = cast(list[Any], raw_details) if isinstance(raw_details, list) else []
            for d_raw in details:
                if isinstance(d_raw, dict):
                    d = cast(dict[str, Any], d_raw)
                    if d.get("status") == "failed":
                        print(f"  - {d.get('path')}: {d.get('reason')}")
            sys.exit(1)
        return 0

    elif update_current:
        _memory_dir = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "infrastructure", "memory"
        ))
        if _memory_dir not in sys.path:
            sys.path.insert(0, _memory_dir)
        from workflow_runtime.infrastructure.memory.update import run_update
        previous_json_output = os.environ.get("AIWF_JSON_OUTPUT")
        if as_json:
            os.environ["AIWF_JSON_OUTPUT"] = "1"
        try:
            res = run_update()
        finally:
            if previous_json_output is None:
                os.environ.pop("AIWF_JSON_OUTPUT", None)
            else:
                os.environ["AIWF_JSON_OUTPUT"] = previous_json_output
        status = "success" if res.get("status") == "success" else "failure"
        if as_json:
            return emit_result(CommandResult(
                command="update",
                status=status,
                summary="Current project memory/update operation completed.",
                data=res,
                side_effects=(".agents/memory",),
                next_action=NextAction(command="doctor"),
            ), sys.stdout)
        if status == "failure":
            sys.exit(1)
        return 0

    return 0


__all__ = [
    "do_update",
]
