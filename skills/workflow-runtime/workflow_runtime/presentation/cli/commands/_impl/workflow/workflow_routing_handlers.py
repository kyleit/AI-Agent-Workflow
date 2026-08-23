from __future__ import annotations

from typing import Any

import argparse
import json
import sys


def do_routing(args: argparse.Namespace) -> None:
    from workflow_runtime.domain.agent.agent_routing import (
        load_routing_table, validate_routing)
    manifest_path = "MANIFEST.json"
    agents_dir = "agents"

    if (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "list":
        table = load_routing_table(manifest_path)
        print("| Skill | Owner | Specialist Agents | Phase | Execution Mode |")
        print("|---|---|---|---|---|")
        for skill_name, info in sorted(table.items()):
            specs = ", ".join(info["specialist_agents"])
            print(f"| {skill_name} | {info['owner_agent']} | {specs} | {info['phase']} | {info['execution_mode']} |")

    elif (getattr(args, 'action', None) or getattr(args, 'subaction', None)) == "validate":
        errors = validate_routing(manifest_path, agents_dir)
        if errors:
            print("Routing validation failed with errors:")
            for err in errors:
                print(f"\u274c {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print("\u2714 Routing validation passed successfully.")


def do_discover_action(args: argparse.Namespace) -> None:
    from workflow_runtime.application.system.project_discovery import \
        run_discovery
    res = run_discovery()
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)


def do_classify_action(args: argparse.Namespace) -> None:
    from workflow_runtime.application.skills.skill_classifier import \
        classify_intent
    res = classify_intent(args.request)
    print(json.dumps(res, indent=2))
    if res["status"] != "success":
        sys.exit(1)


def _run_core_cli_handler(args: Any, handler_name: str) -> Any:  # pyright: ignore[reportUnusedFunction]
    from workflow_runtime.presentation.cli import \
        handlers as core_handlers  # noqa: PLC0415
    handler = getattr(core_handlers, handler_name)
    exit_code = int(handler(args) or 0)
    if exit_code != 0:
        sys.exit(exit_code)