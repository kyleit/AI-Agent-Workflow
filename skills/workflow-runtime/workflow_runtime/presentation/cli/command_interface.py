from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

"""
Command interface definitions for the Command Registry pattern.

Every CLI command must implement the Command protocol:
  - meta()       -> CommandMeta  (name, aliases, category, help, requires_lock)
  - add_parser() -> ArgumentParser (called once at registry build time)
  - parse()      -> Namespace     (called per invocation)
  - run()        -> int|None      (execute the command)
  - print_help() -> None          (detailed help via argparse)
"""


@dataclass
class CommandMeta:
    """
    Static metadata attached to every registered command.

    Attributes:
        name:          Primary CLI name, e.g. "visual", "telegram"
        aliases:       Alternative names, e.g. ["vir", "var"] for visual
        category:      Group label displayed in `aiwf --help` output.
                       Supported: session | workflow | task | dependency |
                       config | runtime | ui | agent | memory | knowledge |
                       visual | telegram | provider | docs | system | testing
        help:          One-line description shown in top-level help
        requires_lock: True = wrap execution in SessionLock context manager
    """

    name: str
    aliases: list[str] = field(default_factory=list[str])
    category: str = "general"
    help: str = ""
    requires_lock: bool = False


@runtime_checkable
class Command(Protocol):
    """
    Duck-typed interface every CLI command MUST implement.

    Lifecycle (called in this order):
      1. build_registry() calls add_parser(subparsers) once at startup
         Command stores its ArgumentParser internally as self._parser
      2. registry.execute() calls parse(argv) then run(args) per invocation
      3. registry.help() calls print_help() for detailed output

    Rules:
      - add_parser() MUST store: self._parser = p
      - parse() MUST delegate: return self._parser.parse_args(argv)
      - run() MUST return int exit code or None (treated as 0)
      - print_help() MUST delegate: self._parser.print_help()
    """

    def meta(self) -> CommandMeta:
        """Return static metadata. Called once at registration."""
        ...

    def add_parser(
        self, subparsers: Any
    ) -> argparse.ArgumentParser:
        """Register argparse subparser. Must store: self._parser = p"""
        ...

    def parse(self, argv: list[str]) -> argparse.Namespace:
        """Parse argv. Delegate: return self._parser.parse_args(argv)"""
        ...

    def run(self, args: argparse.Namespace) -> int | None:
        """Execute command. Return int exit code or None (= 0)."""
        ...

    def print_help(self) -> None:
        """Print detailed help. Delegate: self._parser.print_help()"""
        ...


__all__ = [
    "CommandMeta",
    "Command",
]
