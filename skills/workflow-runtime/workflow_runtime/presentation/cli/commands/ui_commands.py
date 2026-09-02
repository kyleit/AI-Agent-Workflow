from __future__ import annotations

from typing import Any

"""Commands: prompt, input, choice"""

import argparse

from workflow_runtime.presentation.cli.command_interface import CommandMeta


class PromptCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "prompt",
            category="ui",
            help="Interactive prompt: select, confirm, input — for Blueprint approval gates",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("prompt", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")
        sel = sub.add_parser("select", help="Show a selection prompt")
        sel.add_argument("--question", required=True)
        sel.add_argument("--options", required=True,
                         help="Pipe-separated options e.g. 'Continue|Cancel'")
        sel.add_argument("--default", default="Cancel")
        sel.add_argument(
            "--response",
            default=None,
            help="Optional response supplied by the Agent/IDE bridge; avoids stdin interaction.",
        )
        con = sub.add_parser("confirm", help="Show a yes/no confirmation")
        con.add_argument("--question", required=True)
        con.add_argument("--default", choices=["yes", "no"], default="no")
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> int:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_prompt
        return int(do_prompt(args) or 0)

    def print_help(self) -> None: self._parser.print_help()


class InputCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "input",
            category="ui",
            help="Read text input from user or stdin",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("input", help=self.meta().help)
        sub = p.add_subparsers(dest="subaction")  # not required: print help if omitted
        sub_p = sub.add_parser("submit")
        sub_p.add_argument("--input-id", required=True, type=str)
        sub_p.add_argument("--value", required=True, type=str)
        sub_p.add_argument("--source", required=True, type=str)
        sub_p.add_argument("--resume-token", required=True, type=str)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        if not getattr(args, 'subaction', None):
            self._parser.print_help(); return
        from workflow_runtime.presentation.cli.workflow_runtime import do_input
        do_input(args)

    def print_help(self) -> None: self._parser.print_help()


class ChoiceCommand:
    def meta(self) -> CommandMeta:
        return CommandMeta(
            "choice",
            category="ui",
            help="Present a numbered choice menu to the user",
            requires_lock=True,
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p = subparsers.add_parser("choice", help=self.meta().help)
        p.add_argument("--title", help="Menu title")
        p.add_argument("--options", required=True,
                       help="Newline or pipe-separated choices")
        p.add_argument("--default", type=int, default=1)
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace: return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> None:
        from workflow_runtime.presentation.cli.workflow_runtime import \
            do_choice
        do_choice(args)

    def print_help(self) -> None: self._parser.print_help()


def all_commands() -> list[object]:
    return [PromptCommand(), InputCommand(), ChoiceCommand()]
