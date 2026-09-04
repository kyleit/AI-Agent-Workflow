from __future__ import annotations

from typing import Any

"""Commands: cleanup, migrate(+migration)"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class CleanupCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "cleanup",
            category="docs",
            help="Run semantic documentation cleanup and folder migration",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("cleanup", help=self.meta().help)
        p.add_argument("--dry-run", action="store_true",
                       help="Preview changes without writing")
        p.add_argument("--target", help="Target directory to clean")
        p.add_argument("--backup", action="store_true",
                       help="Create backup before cleanup")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_cleanup_action
        do_cleanup_action(args)

    def print_help(self) -> None: self._parser.print_help()


class MigrateCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "migrate",
            aliases=["migration"],
            category="docs",
            help="Migration tools for workflow artifacts and data",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser(
            "migrate",
            aliases=["migration"],
            help=self.meta().help,
        )
        sub = p.add_subparsers(dest="subaction", required=False)
        sub.add_parser("state", help="Migrate state files to new schema")
        sub.add_parser("to-global", help="Switch a legacy project to global-link metadata without deleting copies")
        sub.add_parser("rollback", help="Restore the previous project bridge metadata")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_migration_action
        do_migration_action(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [CleanupCommand(), MigrateCommand()]
