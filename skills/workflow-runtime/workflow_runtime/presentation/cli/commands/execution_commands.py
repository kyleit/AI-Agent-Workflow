from __future__ import annotations

from typing import Any

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class ExecutionCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "execution",
            category="runtime",
            help="Manage execution plans and running processes",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("execution", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("list",   help="List active executions")
        sub.add_parser("status", help="Current execution status")
        sub.add_parser("cancel", help="Cancel running execution")
        sub.add_parser("log",    help="Show execution log")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_execution
        do_execution(args)

    def print_help(self) -> None: self._parser.print_help()


class RuntimeCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "runtime",
            category="runtime",
            help="Runtime daemon and process management",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("runtime", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("start",   help="Start runtime daemon")
        sub.add_parser("stop",    help="Stop runtime daemon")
        sub.add_parser("status",  help="Daemon status")
        sub.add_parser("restart", help="Restart daemon")
        sub.add_parser("reload",  help="Reload daemon")
        sub.add_parser("enable",  help="Enable daemon autostart")
        sub.add_parser("disable", help="Disable daemon autostart")
        sub.add_parser("process", help="Process management")
        sub.add_parser("daemon",  help="Daemon direct operations")

        policy_p = sub.add_parser("policy", help="Manage runtime policy")
        policy_p.add_argument("policy_action", nargs="?", choices=["validate", "reset"], help="Policy action")

        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_runtime_action
        do_runtime_action(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [ExecutionCommand(), RuntimeCommand()]
