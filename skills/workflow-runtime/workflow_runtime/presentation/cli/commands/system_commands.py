from __future__ import annotations

from typing import Any

"""Commands: api-server, doctor, notify, debug, verify, release, gate"""

import argparse
import os
import sys
from pathlib import Path

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class ApiServerCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "api-server",
            category="system",
            help="Start stable Observability API Server",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("api-server", help=self.meta().help)
        p.add_argument("--port", type=int, default=8080)
        p.add_argument("--host", default="127.0.0.1")
        p.add_argument("--debug", action="store_true")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_api_server
        do_api_server(args)

    def print_help(self) -> None: self._parser.print_help()


class DoctorCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "doctor",
            category="system",
            help="Run workspace/framework diagnostics",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("doctor", help=self.meta().help)
        p.add_argument("--fix", action="store_true", help="Auto-fix issues")
        p.add_argument("--verbose", action="store_true")
        p.add_argument("--check", help="Run specific check only")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        import sys

        from workflow_runtime.application.system.workspace_doctor import \
            main as do_doctor
        sys.argv = ["doctor", getattr(args, "path", ".")]
        do_doctor()

    def print_help(self) -> None: self._parser.print_help()


class NotifyCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "notify",
            category="system",
            help="Send Telegram notification",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("notify", help=self.meta().help)
        p.add_argument("--message", "-m", required=True)
        p.add_argument("--level",
                       choices=["info", "warning", "error", "success"],
                       default="info")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_notify_action
        do_notify_action(args)

    def print_help(self) -> None: self._parser.print_help()


class DebugCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "debug",
            category="system",
            help="Debug tools: logs, state dump, diagnostics",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("debug", help=self.meta().help)
        p.add_argument("action", nargs="?",
                       choices=["logs", "state", "session", "memory", "env"])
        p.add_argument("--tail", type=int, default=50)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_debug_action
        do_debug_action(args)

    def print_help(self) -> None: self._parser.print_help()


class VerifyCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "verify",
            category="system",
            help="Verify implementation against blueprint",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("verify", help=self.meta().help)
        p.add_argument("--blueprint", help="Blueprint file path")
        p.add_argument("--strict", action="store_true")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_verify_action
        do_verify_action(args)

    def print_help(self) -> None: self._parser.print_help()


class ReleaseCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "release",
            category="system",
            help="Release pipeline: validate, tag, publish",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("release", help=self.meta().help)
        p.add_argument("action", nargs="?",
                       choices=["validate", "tag", "publish",
                                "rollback", "status", "plan", "execute"])
        p.add_argument("--version")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--approve", action="store_true")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_release_action
        do_release_action(args)

    def print_help(self) -> None: self._parser.print_help()


class PostReleaseCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "post-release",
            category="system",
            help="Post-release lifecycle: validate, monitor, handoff reports",
            aliases=["postrelease"],
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("post-release", help=self.meta().help)
        p.add_argument("action", nargs="?", choices=["run", "status"], default="run")
        p.add_argument("--version", default="0.0.0")
        p.add_argument("--commit", default="HEAD")
        p.add_argument("--output-dir", default="docs/verification")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.commands._impl.system.system_health import \
            do_post_release_action
        do_post_release_action(args)

    def print_help(self) -> None: self._parser.print_help()


class GateCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "gate",
            category="system",
            help="Run the AIWF source-write gate through the global launcher",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("gate", help=self.meta().help)
        p.add_argument("action", nargs="?", choices=["status", "check-git", "check-files", "check-release-tags"], default="status")
        p.add_argument("path", nargs="?")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        project_root = Path.cwd().resolve()
        for candidate in (project_root, *project_root.parents):
            launcher = candidate / "tools" / "aiwf-hooks" / "aiwf_gate_launcher.py"
            if launcher.is_file():
                sys.path.insert(0, str(launcher.parent))
                from aiwf_gate_launcher import run
                argv = [str(getattr(args, "action", "status"))]
                if getattr(args, "path", None):
                    argv.append(str(args.path))
                raise SystemExit(run(argv))
        configured = os.environ.get("AIWF_GLOBAL_ROOT") or os.environ.get("AIWF_FRAMEWORK_ROOT")
        if configured:
            launcher = Path(configured) / "tools" / "aiwf-hooks" / "aiwf_gate_launcher.py"
            if launcher.is_file():
                sys.path.insert(0, str(launcher.parent))
                from aiwf_gate_launcher import run
                raise SystemExit(run([str(getattr(args, "action", "status"))]))
        print("[aiwf-gate] global launcher is unavailable", file=sys.stderr)
        raise SystemExit(4)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [
        ApiServerCommand(),
        DoctorCommand(),
        NotifyCommand(),
        DebugCommand(),
        VerifyCommand(),
        ReleaseCommand(),
        PostReleaseCommand(),
        GateCommand(),
    ]
