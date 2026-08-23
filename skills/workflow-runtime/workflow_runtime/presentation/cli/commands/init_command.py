from __future__ import annotations

import argparse
from typing import Any

from workflow_runtime.presentation.cli.command_interface import CommandMeta

"""Command: init — initialise AIWF workspace."""


class InitCommand:
    """
    aiwf init — initialise AIWF workspace.
    Body (do_init, ~576L) stays in workflow_runtime.py and is delegated via run().
    """

    def __init__(self) -> None:
        self._parser: argparse.ArgumentParser | None = None

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "init",
            category="session",
            help="Initialise AIWF workspace and install skills",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("init", help=self.meta().help)
        p.add_argument("path", nargs="?", default=".", help="Target directory for initialization")
        p.add_argument("--force", action="store_true",
                       help="Force re-initialise existing workspace")
        p.add_argument("--skill", help="Install specific skill only")
        p.add_argument("--template", help="Workspace template to use")
        p.add_argument("--no-git", action="store_true",
                       help="Skip git repository setup")
        p.add_argument("--quiet", action="store_true",
                       help="Minimal output")
        p.add_argument("--non-interactive", action="store_true",
                       help="Run in non-interactive mode")
        p.add_argument("--config", help="Path to config file for non-interactive mode")
        p.add_argument("--resume", action="store_true",
                       help="Resume from previous interactive session draft")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace:
        if self._parser is None:
            raise RuntimeError("Parser not initialized.")
        return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> int | None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_init
        res: Any = do_init(args)
        return int(res) if res is not None else 0

    def print_help(self) -> None:
        if self._parser is not None:
            self._parser.print_help()


def all_commands() -> list[Any]:
    return [InitCommand()]


__all__ = [
    "InitCommand",
    "all_commands",
]
