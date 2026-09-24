from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from workflow_runtime.presentation.cli.command_interface import CommandMeta

"""Command: loop — passthrough to the loop-controller deterministic engine.

This command adds no business logic. It resolves the sibling `loop-controller`
skill's engine package and forwards `load | decide | persist` verbatim, so the
CLI (`aiwf loop ...`), the raw launchers, and PROTOCOL.md hand-execution are all
equivalent (single source of truth = skills/loop-controller/scripts/loop_engine).
"""


def _resolve_loop_scripts() -> Path | None:
    """Return the loop_engine package root (`.../loop-controller/scripts`).

    Tries, in order: the sibling skill in this framework install, an explicit
    AIWF_FRAMEWORK_ROOT, and the active repository's source/mirror trees.
    """
    import os

    candidates: list[Path] = []

    # 1. Sibling skill in the same install as workflow_runtime.
    try:
        import workflow_runtime

        wr_file = getattr(workflow_runtime, "__file__", None)
        if wr_file:
            skills_dir = Path(wr_file).resolve().parents[1].parent
            candidates.append(skills_dir / "loop-controller" / "scripts")
    except (ImportError, IndexError):
        pass

    # 2. Explicit framework root.
    framework_root = os.environ.get("AIWF_FRAMEWORK_ROOT")
    if framework_root:
        root = Path(framework_root)
        candidates.append(root / "skills" / "loop-controller" / "scripts")

    # 3. Active repository trees (source authoritative, then runtime mirror).
    cwd = Path.cwd()
    for base in (cwd, *cwd.parents):
        candidates.append(base / "skills" / "loop-controller" / "scripts")
        candidates.append(
            base / ".agents" / "skills" / "loop-controller" / "scripts"
        )

    for candidate in candidates:
        if (candidate / "loop_engine" / "__init__.py").is_file():
            return candidate
    return None


class LoopCommand:
    def __init__(self) -> None:
        self._parser: argparse.ArgumentParser | None = None

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "loop",
            aliases=["loop-engine"],
            category="workflow",
            help="Run the deterministic loop controller (load|decide|persist)",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p: argparse.ArgumentParser = subparsers.add_parser(
            "loop", help=self.meta().help
        )
        _ = p.add_argument(
            "loop_args",
            nargs=argparse.REMAINDER,
            help="Forwarded to loop_engine: load|decide|persist [flags]",
        )
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace:
        if self._parser is None:
            raise RuntimeError("Parser not initialized.")
        return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> int | None:
        scripts_dir = _resolve_loop_scripts()
        if scripts_dir is None:
            print(
                "loop-controller engine not found. Follow "
                "skills/loop-controller/PROTOCOL.md to run the loop by hand.",
                file=sys.stderr,
            )
            return 3
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from loop_engine.presentation.cli import main as loop_main

        forwarded: list[str] = list(getattr(args, "loop_args", []) or [])
        return loop_main(forwarded)

    def print_help(self) -> None:
        if self._parser is not None:
            self._parser.print_help()


def all_commands() -> list[Any]:
    return [LoopCommand()]


__all__ = [
    "LoopCommand",
    "all_commands",
]
