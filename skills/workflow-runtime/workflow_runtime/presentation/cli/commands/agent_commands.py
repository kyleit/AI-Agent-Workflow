from __future__ import annotations

from typing import Any

"""Command: analysis-agent"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class AnalysisAgentCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "analysis-agent",
            category="agent",
            help="Run analysis agent for code, architecture, or performance review",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("analysis-agent", help=self.meta().help)
        p.add_argument("action", nargs="?",
                       choices=["code", "architecture", "performance",
                                "security", "accessibility"])
        p.add_argument("--target", help="Target file or directory")
        p.add_argument("--output", help="Output report path")
        p.add_argument("--format", choices=["json", "markdown", "text"],
                       default="markdown")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_analysis_agent
        do_analysis_agent(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [AnalysisAgentCommand()]