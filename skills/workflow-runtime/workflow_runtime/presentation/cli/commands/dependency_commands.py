from __future__ import annotations

from typing import Any

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class DepsCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "deps",
            category="dependency",
            help="Runtime dependency resolver commands",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("deps", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("resolve", help="Resolve missing deps")
        sub.add_parser("check",   help="Check deps integrity")
        sub.add_parser("install", help="Install missing deps")
        sub.add_parser("list",    help="List all resolved deps")
        sub.add_parser("status",  help="Deps health status")
        sub.add_parser("inspect", help="Inspect deps")
        sub.add_parser("validate", help="Validate deps")
        p.add_argument("--skill", help="Target skill for deps check")
        p.add_argument("--force", action="store_true")
        p.add_argument("--format", choices=["json", "text", "table"],
                       default="table")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_deps
        do_deps(args)

    def print_help(self) -> None: self._parser.print_help()


class DependencyCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "dependency",
            category="dependency",
            help="Dependency graph analysis and validation",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("dependency", help=self.meta().help)
        p.add_argument("action", nargs="?",
                       choices=["graph", "validate", "scan", "report"])
        p.add_argument("--output", help="Output file path")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_dependency
        do_dependency(args)

    def print_help(self) -> None: self._parser.print_help()


class MergeCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "merge",
            category="dependency",
            help="Merge dependency resolution from multiple agents",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("merge", help=self.meta().help)
        p.add_argument("--from", dest="from_agent", help="Source agent ID")
        p.add_argument("--strategy",
                       choices=["latest", "oldest", "manual"],
                       default="latest")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_merge
        do_merge(args)

    def print_help(self) -> None: self._parser.print_help()


class ConflictCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "conflict",
            category="dependency",
            help="Detect and resolve dependency conflicts",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("conflict", help=self.meta().help)
        p.add_argument("action", nargs="?",
                       choices=["detect", "resolve", "list"])
        p.add_argument("--auto", action="store_true",
                       help="Auto-resolve conflicts")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_conflict
        do_conflict(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [DepsCommand(), DependencyCommand(), MergeCommand(), ConflictCommand()]
