from __future__ import annotations

import argparse
from typing import Any

from workflow_runtime.presentation.cli.command_interface import CommandMeta

"""Command: usage"""


class UsageCommand:
    def __init__(self) -> None:
        self._parser: argparse.ArgumentParser | None = None

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "usage",
            category="session",
            help="Show context window usage, token counts, and budget",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("usage", help=self.meta().help)
        p.add_argument("--format", choices=["json", "table", "text"],
                       default="table")
        p.add_argument("--history", action="store_true",
                       help="Show usage history")
        p.add_argument("--provider", help="Filter by provider")
        p.add_argument("--limit", type=int, default=10)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace:
        if self._parser is None:
            raise RuntimeError("Parser not initialized.")
        return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> int | None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_usage
        res: Any = do_usage(args)
        return int(res) if res is not None else 0

    def print_help(self) -> None:
        if self._parser is not None:
            self._parser.print_help()


def all_commands() -> list[Any]:
    return [UsageCommand()]


__all__ = [
    "UsageCommand",
    "all_commands",
]
