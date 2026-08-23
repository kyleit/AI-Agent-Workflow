from __future__ import annotations

import argparse

from workflow_runtime.presentation.cli.commands._impl.shared_helpers import (
    _run_core_cli_handler)


def do_visual_action(args: argparse.Namespace) -> int:
    res = _run_core_cli_handler("handle_visual", args)
    return int(res) if res is not None else 0


__all__ = [
    "do_visual_action",
]
