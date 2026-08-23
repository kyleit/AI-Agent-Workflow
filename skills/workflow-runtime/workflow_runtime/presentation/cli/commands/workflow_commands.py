from __future__ import annotations

from typing import Any

"""Commands: workflow, active-workflow, coordinator, dispatch, routing,
             discover, classify, orchestrator(+orchestrate)"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class WorkflowCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "workflow",
            category="workflow",
            help="Workflow lifecycle: create, run, status, history",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("workflow", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sub.add_parser("status",  help="Current workflow status")
        sub.add_parser("history", help="Workflow execution history")
        c = sub.add_parser("create", help="Create new workflow")
        c.add_argument("--skill", required=True)
        s = sub.add_parser("submit", help="Submit a raw request to the workflow gateway")
        s.add_argument("--prompt", required=True)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_workflow
        do_workflow(args)

    def print_help(self) -> None: self._parser.print_help()


class ActiveWorkflowCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "active-workflow",
            category="workflow",
            help="Query and manage the currently active workflow",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("active-workflow", help=self.meta().help)
        p.add_argument("--json", action="store_true")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_active_workflow
        do_active_workflow(args)

    def print_help(self) -> None: self._parser.print_help()


class CoordinatorCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "coordinator",
            category="workflow",
            help="Run workflow coordinator tick",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("coordinator", help=self.meta().help)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_coordinator_action
        do_coordinator_action(args)

    def print_help(self) -> None: self._parser.print_help()


class DispatchCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "dispatch",
            category="workflow",
            help="Dispatch an agent task",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("dispatch", help=self.meta().help)
        p.add_argument("--agent", required=True, help="Agent role to dispatch")
        p.add_argument("--task", help="Task description")
        p.add_argument("--skill", help="Target skill")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_dispatch_action
        do_dispatch_action(args)

    def print_help(self) -> None: self._parser.print_help()


class RoutingCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "routing",
            category="workflow",
            help="Show workflow routing and intent classification",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("routing", help=self.meta().help)
        p.add_argument("--intent", help="Raw intent to classify")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_routing
        do_routing(args)

    def print_help(self) -> None: self._parser.print_help()


class DiscoverCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "discover",
            category="workflow",
            help="Discover available workflow skills and capabilities",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("discover", help=self.meta().help)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_discover_action
        do_discover_action(args)

    def print_help(self) -> None: self._parser.print_help()


class ClassifyCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "classify",
            category="workflow",
            help="Classify a user request into workflow intent",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("classify", help=self.meta().help)
        p.add_argument("--request", required=True,
                       help="User request to classify")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_classify_action
        do_classify_action(args)

    def print_help(self) -> None: self._parser.print_help()


class OrchestratorCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "orchestrator",
            aliases=["orchestrate"],
            category="workflow",
            help="Run multi-agent orchestration pipeline",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser(
            "orchestrator",
            aliases=["orchestrate"],
            help=self.meta().help,
        )
        p.add_argument(
            "action",
            nargs="?",
            choices=["run", "status", "cancel", "resume"],
        )
        p.add_argument("--work-item", help="Work item ID")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_orchestrator
        do_orchestrator(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [
        WorkflowCommand(),
        ActiveWorkflowCommand(),
        CoordinatorCommand(),
        DispatchCommand(),
        RoutingCommand(),
        DiscoverCommand(),
        ClassifyCommand(),
        OrchestratorCommand(),
    ]
