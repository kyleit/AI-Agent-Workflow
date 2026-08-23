from __future__ import annotations

from typing import Any

"""Command: test — run test suite"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class TestCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "test",
            category="testing",
            help="Run test suite: unit, smoke, integration, real-runtime checks",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("test", help=self.meta().help)
        p.add_argument(
            "scope",
            nargs="?",
            choices=["unit", "smoke", "integration", "all", "real"],
            default="smoke",
            help="Test scope (default: smoke)",
        )
        p.add_argument("--verbose", "-v", action="store_true")
        p.add_argument("--fail-fast", action="store_true",
                       help="Stop on first failure")
        p.add_argument("--output", help="Output report path")
        p.add_argument("--filter", "-k",
                       help="Filter tests by name pattern")
        p.add_argument("--log", help="Log file path (default: .agents/runtime/tests.log)")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_test_action
        do_test_action(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [TestCommand()]