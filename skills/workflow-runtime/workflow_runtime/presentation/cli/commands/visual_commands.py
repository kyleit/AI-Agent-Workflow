from __future__ import annotations

from typing import Any

"""Command: visual (+vir, +var aliases) — Visual Intelligence Runtime"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class VisualCommand:
    """
    Visual Intelligence Runtime — VIR/VAR operations.
    Aliases: vir, var -> all map to the same VisualCommand instance.
    """

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "visual",
            aliases=["vir", "var"],
            category="visual",
            help="Visual Intelligence Runtime — capture, inspect, verify UI",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser(
            "visual",
            aliases=["vir", "var"],
            help=self.meta().help,
        )
        visual_sub = p.add_subparsers(dest="subcommand")  # not required: print help if omitted
        for visual_action in ["agent", "investigate", "verify", "memory", "report", "observe"]:
            visual_action_p = visual_sub.add_parser(visual_action)
            visual_action_p.add_argument("--url", type=str, default=None)
            visual_action_p.add_argument("--goal", type=str, default=None)
            visual_action_p.add_argument("--max-iter", type=int, default=3)
            visual_action_p.add_argument("--mode", choices=["cli", "ipc", "daemon"], default="cli")
            visual_action_p.add_argument("--feature-id", type=str, default="FEAT-000")
            visual_action_p.add_argument("--ci", action="store_true")
        e2e = visual_sub.add_parser("e2e", help="Run the required frontend visual E2E loop")
        e2e.add_argument("--url", required=True)
        e2e.add_argument("--feature-id", required=True)
        e2e.add_argument("--route", default="/")
        e2e.add_argument("--max-iterations", type=int, default=8)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace:
        return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> int:
        if not getattr(args, 'subcommand', None):
            self._parser.print_help(); return 0
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_visual_action
        return do_visual_action(args)

    def print_help(self) -> None:
        self._parser.print_help()


def all_commands() -> list[object]:
    return [VisualCommand()]
