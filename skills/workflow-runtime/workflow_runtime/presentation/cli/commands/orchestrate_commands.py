from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from workflow_runtime.presentation.cli.command_interface import CommandMeta

"""Command: orchestrate — passthrough to the multi-agent-loop (MALO) engine.

No business logic: it resolves the sibling `multi-agent-loop` skill's engine and
forwards `select | run` verbatim, so the CLI (`aiwf orchestrate ...`), the raw
launcher, and PROTOCOL.md hand-execution are all equivalent.
"""


def _resolve_malo_scripts() -> Path | None:
    import os

    candidates: list[Path] = []
    try:
        import workflow_runtime

        wr_file = getattr(workflow_runtime, "__file__", None)
        if wr_file:
            skills_dir = Path(wr_file).resolve().parents[1].parent
            candidates.append(skills_dir / "multi-agent-loop" / "scripts")
    except (ImportError, IndexError):
        pass

    framework_root = os.environ.get("AIWF_FRAMEWORK_ROOT")
    if framework_root:
        candidates.append(
            Path(framework_root) / "skills" / "multi-agent-loop" / "scripts"
        )

    cwd = Path.cwd()
    for base in (cwd, *cwd.parents):
        candidates.append(base / "skills" / "multi-agent-loop" / "scripts")
        candidates.append(
            base / ".agents" / "skills" / "multi-agent-loop" / "scripts"
        )

    for candidate in candidates:
        if (candidate / "malo" / "__init__.py").is_file():
            return candidate
    return None


class OrchestrateCommand:
    def __init__(self) -> None:
        self._parser: argparse.ArgumentParser | None = None

    def meta(self) -> CommandMeta:
        return CommandMeta(
            "malo",
            aliases=["agent-loop"],
            category="workflow",
            help="Drive the multi-agent loop (select|run) across Claude/Codex/Antigravity",
        )

    def add_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        p: argparse.ArgumentParser = subparsers.add_parser(
            "malo", help=self.meta().help
        )
        _ = p.add_argument(
            "malo_args",
            nargs=argparse.REMAINDER,
            help="Forwarded to the MALO engine: select|run [flags]",
        )
        self._parser = p
        return p

    def parse(self, argv: list[str]) -> argparse.Namespace:
        if self._parser is None:
            raise RuntimeError("Parser not initialized.")
        return self._parser.parse_args(argv)

    def run(self, args: argparse.Namespace) -> int | None:
        scripts_dir = _resolve_malo_scripts()
        if scripts_dir is None:
            print(
                "multi-agent-loop engine not found. Follow "
                "skills/multi-agent-loop/PROTOCOL.md to run the loop by hand.",
                file=sys.stderr,
            )
            return 3
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        from malo.presentation.cli import main as malo_main

        forwarded: list[str] = list(getattr(args, "malo_args", []) or [])
        return malo_main(forwarded)

    def print_help(self) -> None:
        if self._parser is not None:
            self._parser.print_help()


def all_commands() -> list[Any]:
    return [OrchestrateCommand()]


__all__ = [
    "OrchestrateCommand",
    "all_commands",
]
