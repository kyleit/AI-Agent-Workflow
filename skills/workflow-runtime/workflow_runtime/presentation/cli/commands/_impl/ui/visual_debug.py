from __future__ import annotations

import argparse

from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    _run_core_cli_handler)


def do_visual_action(args: argparse.Namespace) -> int:
    if getattr(args, "subcommand", None) == "e2e":
        import json
        from workflow_runtime.application.verification.frontend_e2e_gate import run_frontend_e2e

        result = run_frontend_e2e(
            url=args.url,
            feature_id=args.feature_id,
            route=args.route,
            max_iterations=args.max_iterations,
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result.get("status") == "PASS" else 2
    res = _run_core_cli_handler("handle_visual", args)
    return int(res) if res is not None else 0


__all__ = [
    "do_visual_action",
]
