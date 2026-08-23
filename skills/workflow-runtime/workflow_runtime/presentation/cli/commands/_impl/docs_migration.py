from __future__ import annotations

import argparse
import json
import sys
from workflow_runtime.presentation.cli.commands._impl.context_manager import (
    do_state_action)
from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    _run_core_cli_handler)


def do_cleanup_action(args: argparse.Namespace) -> int:
    res = _run_core_cli_handler("handle_cleanup", args)
    return int(res) if res is not None else 0


def do_migration_action(args: argparse.Namespace) -> int:
    subaction = getattr(args, 'action', None) or getattr(args, 'subaction', None)
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
