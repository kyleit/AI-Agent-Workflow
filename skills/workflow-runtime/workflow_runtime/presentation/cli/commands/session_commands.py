from __future__ import annotations

from typing import Any

"""Commands: start, step, complete, fail, heartbeat, status, resume, lock"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class StartCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "start",
            category="session",
            help="Start a new workflow session checkpoint",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("start", help=self.meta().help)
        p.add_argument("--skill", required=True, help="Skill name to start")
        p.add_argument("--command", required=True, help="Command being executed")
        p.add_argument("--checkpoint", type=int, default=1)
        p.add_argument("--step", default="Starting...")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_start
        do_start(args)

    def print_help(self) -> None: self._parser.print_help()


class StepCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "step",
            category="session",
            help="Update current step description and log",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("step", help=self.meta().help)
        p.add_argument("--step", required=True, help="Step description")
        p.add_argument("--log", default="", help="Log message")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_step
        do_step(args)

    def print_help(self) -> None: self._parser.print_help()


class CompleteCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "complete",
            category="session",
            help="Mark current phase as complete",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("complete", help=self.meta().help)
        p.add_argument("--checkpoint", type=int)
        p.add_argument("--step", default="Complete")
        p.add_argument("--next-skill")
        p.add_argument("--next-command")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_complete
        do_complete(args)

    def print_help(self) -> None: self._parser.print_help()


class FailCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "fail",
            category="session",
            help="Mark current phase as failed",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("fail", help=self.meta().help)
        p.add_argument("--step")
        p.add_argument("--log", default="")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_fail
        do_fail(args)

    def print_help(self) -> None: self._parser.print_help()


class HeartbeatCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "heartbeat",
            category="session",
            help="Update session heartbeat timestamp",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("heartbeat", help=self.meta().help)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_heartbeat
        do_heartbeat(args)

    def print_help(self) -> None: self._parser.print_help()


class StatusCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "status",
            category="session",
            help="Show current workflow session status",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("status", help=self.meta().help)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_status_action
        do_status_action(args)

    def print_help(self) -> None: self._parser.print_help()


class ResumeCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "resume",
            category="session",
            help="Resume workflow from last checkpoint",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("resume", help=self.meta().help)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_resume_action
        do_resume_action(args)

    def print_help(self) -> None: self._parser.print_help()


class LockCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "lock",
            category="session",
            help="Manage workflow session lock",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("lock", help=self.meta().help)
        p.add_argument(
            "action",
            choices=["acquire", "release", "list", "inspect", "recover", "status", "force-release"],
        )
        p.add_argument("--task-id", type=str)
        p.add_argument("--files", type=str)
        p.add_argument("--stale-only", action="store_true")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import do_lock
        do_lock(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [
        StartCommand(),
        StepCommand(),
        CompleteCommand(),
        FailCommand(),
        HeartbeatCommand(),
        StatusCommand(),
        ResumeCommand(),
        LockCommand(),
    ]
