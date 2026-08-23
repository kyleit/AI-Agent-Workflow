from __future__ import annotations

from typing import Any

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class SessionMetaCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "session",
            category="session",
            help="Session management: show, clean, list, delete",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("session", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("show",  help="Show active session info")
        sub.add_parser("list",  help="List all sessions")
        sub.add_parser("clean", help="Clean stale sessions")
        d = sub.add_parser("delete", help="Delete a session")
        d.add_argument("--id", required=True, help="Session ID")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_session_command
        do_session_command(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [SessionMetaCommand()]
