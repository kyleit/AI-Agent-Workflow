from __future__ import annotations

from typing import Any

"""Commands: validate, context, state"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class ValidateCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "validate",
            category="session",
            help="Validate checkpoints, specs, and design artifacts",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("validate", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        bp = sub.add_parser("blueprint", help="Validate a technical blueprint")
        bp.add_argument("--file", required=True, help="Path to blueprint file")
        art = sub.add_parser("artifact", help="Validate a workflow artifact")
        art.add_argument("--file", required=True, help="Path to artifact file")
        sub.add_parser("session", help="Validate active session health")
        p.add_argument("--checkpoint", help="Checkpoint number to validate")
        p.add_argument("--spec", help="Spec file path")
        p.add_argument("--strict", action="store_true")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_validate
        do_validate(args)

    def print_help(self) -> None: self._parser.print_help()


class ContextCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "context",
            category="session",
            help="Show or refresh current context health",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("context", help=self.meta().help)
        p.add_argument("--refresh", action="store_true")
        p.add_argument("--format", choices=["json", "text"], default="text")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_context
        do_context(args)

    def print_help(self) -> None: self._parser.print_help()


class StateCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "state",
            category="session",
            help="Read/write workflow state files",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("state", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("status", help="Status")
        sub.add_parser("recover", help="Recover")
        sub.add_parser("validate", help="Validate")
        sub.add_parser("doctor", help="Doctor")
        sub.add_parser("snapshot", help="Snapshot")
        sub.add_parser("migrate", help="Migrate")
        sub.add_parser("aggregate", help="Aggregate")
        sub.add_parser("emit", help="Emit")
        sub.add_parser("diagnose", help="Diagnose")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_state_action
        do_state_action(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [ValidateCommand(), ContextCommand(), StateCommand()]
