#!/usr/bin/env python3
"""Claude Code PreToolUse hook — AIWF edit-time source-write guard.

Registered against Edit|Write|MultiEdit|NotebookEdit. Reads the Claude hook
JSON payload from stdin, extracts the target file path, and delegates the
allow/deny decision to the shared gate (aiwf_gate.py). This keeps a single
source of truth shared with the git hooks.

Exit codes (Claude Code contract):
  0  -> allow the tool call
  2  -> DENY the tool call (stderr shown to the model)

Self-gating: if the project is not an AIWF project, or the path is not source
code, the hook allows silently. Never blocks non-AIWF projects.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import aiwf_gate as gate  # noqa: E402


def _extract_paths(payload: dict) -> list[str]:
    ti = payload.get("tool_input") or {}
    paths: list[str] = []
    for key in ("file_path", "path", "notebook_path"):
        v = ti.get(key)
        if isinstance(v, str) and v:
            paths.append(v)
    # MultiEdit / batched shapes
    edits = ti.get("edits")
    if isinstance(edits, list):
        fp = ti.get("file_path")
        if isinstance(fp, str) and fp:
            paths.append(fp)
    return paths


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # no/invalid payload -> do not interfere

    if not isinstance(payload, dict):
        return 0

    cwd = payload.get("cwd") or None
    root = gate.repo_root(Path(cwd) if cwd else None)
    if not root or not gate.is_aiwf_project(root):
        return 0

    paths = _extract_paths(payload)
    if not paths:
        return 0

    src = [p for p in paths if gate.is_source_file(root, p)]
    if not src:
        return 0

    if gate._bypassed():
        return 0

    ok, reason = gate.authorization_status(root)
    if ok:
        return 0

    sys.stderr.write(gate.BLOCK_BANNER)
    sys.stderr.write("  Claude edit blocked by AIWF source-write gate.\n")
    sys.stderr.write(f"  Reason: {reason}\n\n")
    sys.stderr.write("  Target(s):\n")
    for p in src:
        sys.stderr.write(f"    - {p}\n")
    sys.stderr.write("\n" + gate.HELP_TEXT)
    sys.stderr.write("==================================================================\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
