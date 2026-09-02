"""Commands: update, self-upgrade, and update-source."""

from __future__ import annotations

import argparse
from typing import Any

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class UpdateCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "update",
            category="system",
            help="Update AIWF framework, skills, and runtime components",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("update", help=self.meta().help)
        p.add_argument("action", nargs="?",
                       choices=["framework", "skills", "runtime", "all"])
        p.add_argument("--force", "-Force", action="store_true")
        p.add_argument("--all", "-All", action="store_true")
        p.add_argument("--current", "-Current", action="store_true")
        p.add_argument("--json", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--check", action="store_true")
        p.add_argument("--yes", action="store_true")
        p.add_argument("--version", help="Target version")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_update
        do_update(args)

    def print_help(self) -> None: self._parser.print_help()


class UpdateSourceCommand:
    """
    update-source: Update source code from remote.
    Body (do_update_source, ~761L) stays in workflow_runtime.py and
    will be split into _impl/update_source_impl.py parts during P4.
    """

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "update-source",
            aliases=["self-upgrade", "upgrade"],
            category="system",
            help="Update the global workflow-runtime source from GitHub",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("update-source", help=self.meta().help)
        p.add_argument("--branch", help="Target branch")
        p.add_argument("--tag", help="Target tag")
        p.add_argument("--source-path", dest="source_path", help="Framework source path")
        p.add_argument("--url", help="Canonical source repository URL")
        p.add_argument("--remote", help="Git remote name")
        p.add_argument("--check", action="store_true")
        p.add_argument("--yes", action="store_true")
        p.add_argument("--json", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--no-install", action="store_true",
                       help="Skip pip install after update")
        p.add_argument("--allow-dirty", action="store_true",
                       help="Ignore local uncommitted changes when updating")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_update_source
        do_update_source(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [UpdateCommand(), UpdateSourceCommand()]
