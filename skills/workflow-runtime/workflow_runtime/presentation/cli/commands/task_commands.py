from __future__ import annotations

from typing import Any

"""Commands: task, blueprint, suggest, compact, work-item, project, implement"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class TaskCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "task",
            category="task",
            help="Task orchestration: create, list, update, complete tasks",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("task", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("list",   help="List tasks")
        sub.add_parser("status", help="Task status")
        c = sub.add_parser("create", help="Create a task")
        c.add_argument("--name", required=True)
        c.add_argument("--agent", required=True)
        u = sub.add_parser("update", help="Update a task")
        u.add_argument("--id", required=True)
        u.add_argument("--status")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_task_orchestrator
        do_task_orchestrator(args)

    def print_help(self) -> None: self._parser.print_help()


class BlueprintCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "blueprint",
            category="task",
            help="Generate or validate technical design blueprint",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("blueprint", help=self.meta().help)
        p.add_argument("action", nargs="?",
                       choices=["generate", "validate", "freeze", "status", "retire"])
        p.add_argument("--path", help="Blueprint file path")
        p.add_argument("--work-item", help="Work item ID")
        p.add_argument("--skill", help="Target skill")
        p.add_argument("--approve", action="store_true", help="Record explicit blueprint approval")
        p.add_argument("--reason", help="Required for retire; persisted in the lifecycle tombstone")
        p.add_argument("--replacement", help="Replacement work-item ID for a superseded blueprint")
        p.add_argument("--json", action="store_true", help="Emit a machine-readable result")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_blueprint
        do_blueprint(args)

    def print_help(self) -> None: self._parser.print_help()


class SuggestCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "suggest",
            category="task",
            help="Suggest next actions based on current workflow state",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("suggest", help=self.meta().help)
        p.add_argument("--limit", type=int, default=5)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_suggest
        do_suggest(args)

    def print_help(self) -> None: self._parser.print_help()


class CompactCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "compact",
            category="task",
            help="Compact session context to reduce token usage",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("compact", help=self.meta().help)
        p.add_argument("--target-tokens", type=int)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_compact
        do_compact(args)

    def print_help(self) -> None: self._parser.print_help()


class WorkItemCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "work-item",
            category="task",
            help="Get cached work item info (fast, no lock needed)",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("work-item", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("detect")
        p.add_argument("--id", help="Work item ID")
        p.add_argument("--format", choices=["json", "text"], default="text")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_work_item_cached
        do_work_item_cached(args)

    def print_help(self) -> None: self._parser.print_help()


class ProjectCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "project",
            category="task",
            help="Get cached project version info",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("project", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("version")
        p.add_argument("--format", choices=["json", "text"], default="text")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_project_version_cached
        do_project_version_cached(args)

    def print_help(self) -> None: self._parser.print_help()


class ImplementCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "implement",
            category="task",
            help="Start implementation from an approved blueprint",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("implement", help=self.meta().help)
        p.add_argument("--blueprint", required=True, help="Blueprint file path")
        p.add_argument("--dry-run", action="store_true")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_implement_action
        do_implement_action(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [
        TaskCommand(),
        BlueprintCommand(),
        SuggestCommand(),
        CompactCommand(),
        WorkItemCommand(),
        ProjectCommand(),
        ImplementCommand(),
    ]
