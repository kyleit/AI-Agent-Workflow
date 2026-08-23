from __future__ import annotations

import argparse
from typing import Any

from workflow_runtime.presentation.cli.command_interface import CommandMeta

"""Command: provider — AI provider management"""


class ProviderCommand:
    """
    AI Provider management: list, select, configure, test, usage.
    Implementation body (do_provider_action, ~794L) stays in workflow_runtime.py
    and is split into _impl/provider_impl.py + _impl/provider_impl_b.py during P4.
    """

    def __init__(self) -> None:
        self._parser: argparse.ArgumentParser | None = None

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "provider",
            aliases=[],
            category="provider",
            help="AI provider management: list, select, configure, test, usage",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("provider", help=self.meta().help)
        p.add_argument(
            "action",
            nargs="?",
            choices=["list", "select", "config", "test", "usage",
                     "status", "reset", "add", "remove"],
            help="Provider action",
        )
        p.add_argument("--name", help="Provider name")
        p.add_argument("--model", help="Model name")
        p.add_argument("--api-key", help="API key (stored securely)")
        p.add_argument("--base-url", help="Custom base URL")
        p.add_argument("--timeout", type=int, default=30)
        p.add_argument("--format", choices=["json", "table", "text"],
                       default="table")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace:
        if self._parser is None:
            raise RuntimeError("Parser not initialized.")
        return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> int | None:
        from workflow_runtime.presentation.cli.workflow_runtime import (
            do_provider_action)
        res: Any = do_provider_action(args)
        return int(res) if res is not None else 0

    def print_help(self) -> None:
        if self._parser is not None:
            self._parser.print_help()


def all_commands() -> list[Any]:
    return [ProviderCommand()]


__all__ = [
    "ProviderCommand",
    "all_commands",
]
