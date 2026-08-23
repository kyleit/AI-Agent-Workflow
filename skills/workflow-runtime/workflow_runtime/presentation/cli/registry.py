from __future__ import annotations

import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from .command_interface import Command, CommandMeta


class CommandRegistry:
    """
    Central registry. Two public methods:
      execute(subcommand, *args, **kwargs) -> int
      help(subcommand=None) -> None
    """

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}
        self._meta: dict[str, CommandMeta] = {}
        self._parser: Any = None

    def register(self, command: Command) -> None:
        meta = command.meta()
        if meta.name in self._meta:
            raise ValueError(
                f"Command '{meta.name}' already registered. "
                f"Check all_commands() for duplicate entries."
            )
        self._commands[meta.name] = command
        self._meta[meta.name] = meta
        for alias in meta.aliases:
            self._commands[alias] = command

    def build_parser(self) -> Any:
        import argparse

        first_cmd = next(iter(self._commands.values()), None)
        if first_cmd and getattr(first_cmd, '_parser', None) is not None:
            return self._parser

        parser = argparse.ArgumentParser(prog="aiwf", add_help=False)
        subparsers: Any = parser.add_subparsers(dest="command")

        seen: set[str] = set()
        for cmd in self._commands.values():
            cmd_meta = cmd.meta()
            if cmd_meta.name not in seen:
                seen.add(cmd_meta.name)
                add_p_fn: Any = getattr(cmd, "add_parser", None)
                if callable(add_p_fn):
                    add_p_fn(subparsers)
        self._parser = parser
        return parser

    def execute(self, subcommand: str, *args: str, **kwargs: Any) -> int:
        cmd = self._commands.get(subcommand)
        if cmd is None:
            print(
                f"Unknown command: '{subcommand}'. Run 'aiwf --help'.",
                file=sys.stderr,
            )
            return 2

        self.build_parser()

        argv: list[str] = list(args)
        for key, value in kwargs.items():
            flag = f"--{key.replace('_', '-')}"
            if isinstance(value, bool):
                if value:
                    argv.append(flag)
            elif value is not None:
                argv.extend([flag, str(value)])

        parsed = cmd.parse(argv)

        _chdir_to_aiwf_project_root_if_needed()

        if cmd.meta().requires_lock:
            from workflow_runtime.infrastructure.session.session import (
                SessionLock)
            with SessionLock():
                result = cmd.run(parsed)
        else:
            result = cmd.run(parsed)

        return int(result or 0)

    def help(self, subcommand: str | None = None) -> None:
        if subcommand is not None:
            cmd = self._commands.get(subcommand)
            if cmd is None:
                print(f"Unknown command: '{subcommand}'", file=sys.stderr)
                return
            cmd.print_help()
        else:
            self._print_top_level_help()

    def _print_top_level_help(self) -> None:
        print("AI Workflow Runtime Engine CLI")
        print("Usage: aiwf <command> [args] [--option=value ...]\n")

        groups: dict[str, list[CommandMeta]] = defaultdict(list)
        seen: set[str] = set()
        for name, meta in sorted(self._meta.items()):
            if name not in seen:
                seen.add(name)
                groups[meta.category].append(meta)

        for category in sorted(groups.keys()):
            print(f"  {category.upper()}")
            sorted_metas = sorted(groups[category], key=lambda m: str(m.name))
            for meta in sorted_metas:
                aliases_str = (
                    f"  (alias: {', '.join(meta.aliases)})"
                    if meta.aliases
                    else ""
                )
                print(f"    {meta.name:<28} {meta.help}{aliases_str}")
            print()

        print("Run 'aiwf <command> --help' for detailed options.")

    def get_all(self) -> list[Command]:
        seen: set[str] = set()
        result: list[Command] = []
        for cmd in self._commands.values():
            primary = cmd.meta().name
            if primary not in seen:
                seen.add(primary)
                result.append(cmd)
        return result


def _is_aiwf_project_root(path: str) -> bool:
    return os.path.exists(os.path.join(path, ".agents", "AI_RULES.md")) or os.path.exists(os.path.join(path, "AI_RULES.md"))


def _resolve_aiwf_project_root() -> str:
    cwd = os.path.abspath(".")
    if _is_aiwf_project_root(cwd):
        return cwd
    probe = Path(__file__).resolve()
    for parent in probe.parents:
        if parent.name == ".agents":
            return str(parent.parent)
        if parent.name == "public_export":
            return str(parent.parent)
        if _is_aiwf_project_root(str(parent)):
            return str(parent)
    try:
        from workflow_runtime.application.workflow import aiwf_registry

        registry = aiwf_registry.load_registry()
        raw_projects = registry.get("projects", [])
        projects: list[Any] = cast(list[Any], raw_projects) if isinstance(raw_projects, list) else []
        for project in projects:
            if isinstance(project, dict):
                proj_dict = cast(dict[str, Any], project)
                path = str(proj_dict.get("path", "") or "")
                if path and os.path.exists(path) and _is_aiwf_project_root(path):
                    return os.path.abspath(path)
    except Exception:
        pass
    return cwd


def _chdir_to_aiwf_project_root_if_needed() -> None:
    target = _resolve_aiwf_project_root()
    if os.path.abspath(".") != target:
        os.chdir(target)


__all__ = ["CommandRegistry"]
