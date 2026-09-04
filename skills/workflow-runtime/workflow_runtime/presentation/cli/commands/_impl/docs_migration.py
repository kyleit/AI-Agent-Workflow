from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from workflow_runtime.presentation.cli.commands._impl.context_manager import (
    do_state_action)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    _run_core_cli_handler)


def do_cleanup_action(args: argparse.Namespace) -> int:
    res = _run_core_cli_handler("handle_cleanup", args)
    return int(res) if res is not None else 0


def do_migration_action(args: argparse.Namespace) -> int:
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)
    if subaction in ("to-global", "rollback"):
        from workflow_runtime.application.system.project_bridge import (
            migrate_project_to_global, rollback_project_bridge,
        )
        try:
            if subaction == "to-global":
                bridge, backup = migrate_project_to_global(Path.cwd())
                payload = {
                    "status": "success", "code": "PROJECT_MIGRATED_TO_GLOBAL",
                    "bridge": bridge.__dict__, "backup": backup,
                    "side_effects": [".agents/project.json", ".agents/runtime-link.json", backup],
                    "next_action": {"command": "aiwf doctor", "required": False},
                }
            else:
                bridge = rollback_project_bridge(Path.cwd())
                payload = {
                    "status": "success", "code": "PROJECT_BRIDGE_ROLLED_BACK",
                    "bridge": bridge.__dict__ if bridge else None,
                    "side_effects": [".agents/project.json", ".agents/runtime-link.json"],
                    "next_action": {"command": "aiwf doctor", "required": False},
                }
        except (OSError, ValueError) as exc:
            payload = {
                "status": "blocked", "code": str(exc),
                "blocking_findings": [str(exc)],
                "next_action": {"command": "aiwf doctor", "required": True},
            }
            print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
            return 3
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        return 0
    if subaction in (None, "state"):
        setattr(args, "subaction", "migrate")
        res = do_state_action(args)
        return int(res) if res is not None else 0
    print(json.dumps({"status": "failed", "error": f"Unknown migration subaction: {subaction}"}, indent=2))
    sys.exit(2)


__all__ = [
    "do_cleanup_action",
    "do_migration_action",
]
