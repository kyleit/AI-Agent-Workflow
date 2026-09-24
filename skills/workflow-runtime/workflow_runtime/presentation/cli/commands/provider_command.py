from __future__ import annotations

import argparse
from typing import Any

from workflow_runtime.presentation.cli.command_interface import CommandMeta

"""Command: provider — knowledge provider management"""


class ProviderCommand:
    """
    Knowledge provider management (``~/.aiwf/providers.json`` + project overrides).
    Handler: ``_impl/provider/provider_config.py``. ``select``/``usage``/``reset``
    stay in ``choices`` because CLI_REFERENCE.md lists them; they exit 2.
    """

    def __init__(self) -> None:
        self._parser: argparse.ArgumentParser | None = None

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "provider",
            aliases=[],
            category="provider",
            help="Knowledge provider management: list, config, status, test, sync",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("provider", help=self.meta().help)
        p.add_argument(
            "action",
            nargs="?",
            choices=["list", "select", "config", "test", "usage",
                     "status", "reset", "add", "remove", "edit", "enable",
                     "disable", "resolve", "sync", "path", "doctor"],
            help="Provider action",
        )
        p.add_argument("target", nargs="?", help="Provider name (same as --name)")
        p.add_argument("--name", help="Provider name")
        p.add_argument("--project", action="store_true",
                       help="Operate on project overrides (.agents/memory.config.json)")
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
