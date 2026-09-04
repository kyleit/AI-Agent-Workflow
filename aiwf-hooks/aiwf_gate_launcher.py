#!/usr/bin/env python3
"""AI/IDE-facing gate launcher with project and global-root discovery.

The launcher is intentionally stdlib-only. A packaged ``aiwf`` runtime may
invoke the same entry point without depending on the project's Python setup.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    probe = (start or Path.cwd()).resolve()
    # A blank AIWF workspace may live inside another Git repository. Prefer
    # its nearest local marker so a gate never evaluates the parent project.
    if (
        (probe / ".agents" / "AI_RULES.md").is_file()
        or (probe / "AI_RULES.md").is_file()
        or (probe / ".agents" / "project.config.json").is_file()
    ):
        return probe
    # Without a local AIWF marker, keep the caller's workspace boundary. A
    # parent Git repository may be a different project entirely.
    return probe


def _global_candidates(project_root: Path) -> tuple[Path, ...]:
    home = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or Path.home())
    values = (
        os.environ.get("AIWF_GLOBAL_SOURCE"),
        os.environ.get("AIWF_GLOBAL_ROOT"),
        os.environ.get("AIWF_FRAMEWORK_ROOT"),
        os.environ.get("AIWF_HOME"),
        str(home / ".aiwf" / "source"),
        str(home / "AppData" / "Local" / "aiwf" / "source"),
    )
    candidates: list[Path] = []
    for value in values:
        if not value:
            continue
        candidate = Path(value).expanduser().resolve()
        if candidate.name == "source" and not (candidate / "tools" / "aiwf-hooks" / "aiwf_gate.py").is_file():
            nested = candidate / "AI-Agent-Workflow"
            if nested.exists():
                candidate = nested
        if candidate != project_root and candidate not in candidates:
            candidates.append(candidate)
    return tuple(candidates)


def locate_gate(project_root: Path, global_root: Path | None = None) -> Path:
    """Resolve the authoritative gate without assuming a copied project layout."""
    roots = tuple(root for root in (global_root, *_global_candidates(project_root)) if root)
    candidates = tuple(
        candidate
        for root in roots
        for candidate in (
            root / "tools" / "aiwf-hooks" / "aiwf_gate.py",
            root / ".agents" / "aiwf-hooks" / "aiwf_gate.py",
        )
    ) + (
        project_root / ".agents" / "aiwf-hooks" / "aiwf_gate.py",
        project_root / "tools" / "aiwf-hooks" / "aiwf_gate.py",
    )
    for candidate in candidates:
        if candidate.is_file() and candidate.resolve() != Path(__file__).resolve():
            return candidate.resolve()
    raise FileNotFoundError("AIWF gate implementation is unavailable")


def _runtime_command() -> str:
    configured = os.environ.get("AIWF_RUNTIME_EXECUTABLE")
    if configured and Path(configured).is_file():
        return configured
    return sys.executable


def run(argv: list[str] | None = None) -> int:
    project_root = find_project_root()
    gate = locate_gate(project_root)
    command = [_runtime_command(), str(gate), *(argv or sys.argv[1:])]
    completed = subprocess.run(command, cwd=project_root, check=False)
    return int(completed.returncode)


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except (FileNotFoundError, OSError) as exc:
        print(f"[aiwf-gate] launcher unavailable: {exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
