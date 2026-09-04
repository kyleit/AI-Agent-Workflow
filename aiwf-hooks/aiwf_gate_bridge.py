#!/usr/bin/env python3
"""Bridge installed in a project that has no copied ``tools/`` tree."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    for parent in Path(__file__).resolve().parents:
        launcher = parent / ".agents" / "aiwf-hooks" / "aiwf_gate_launcher.py"
        if launcher.is_file():
            sys.path.insert(0, str(launcher.parent))
            from aiwf_gate_launcher import main as launch
            return int(launch(sys.argv[1:]))
    print("[aiwf-gate] project bridge cannot find the global AIWF launcher", file=sys.stderr)
    return 4


if __name__ == "__main__":
    raise SystemExit(main())
