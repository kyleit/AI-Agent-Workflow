from __future__ import annotations

from typing import Any

"""Commands: memory, env, mail"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class MemoryCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "memory",
            category="memory",
            help="Project memory: bootstrap, update, query, status",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("memory", help=self.meta().help)
        p.add_argument(
            "subaction",
            nargs="?",
            choices=["bootstrap", "update", "query", "status", "reset", "export"],
            help="Memory action to perform",
        )
        p.add_argument("--query", help="Search query for memory lookup")
        p.add_argument("--limit", type=int, default=10,
                       help="Max results to return")
        p.add_argument("--format", choices=["json", "text", "table"],
                       default="text")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_memory_action
        do_memory_action(args)

    def print_help(self) -> None: self._parser.print_help()


class EnvCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "env",
            category="memory",
            help="Show runtime environment variables and config",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("env", help=self.meta().help)
        p.add_argument("--filter", help="Filter by key prefix")
        p.add_argument("--json", action="store_true", help="Output as JSON")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_env_action
        do_env_action(args)

    def print_help(self) -> None: self._parser.print_help()


class MailCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "mail",
            category="memory",
            help="Inter-session mail: send, read, list messages",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("mail", help=self.meta().help)
        p.add_argument("subaction", choices=["register", "send", "read", "list"])
        p.add_argument("--to", type=str, default=None)
        p.add_argument("--message", type=str, default=None)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_mail_action
        do_mail_action(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [MemoryCommand(), EnvCommand(), MailCommand()]