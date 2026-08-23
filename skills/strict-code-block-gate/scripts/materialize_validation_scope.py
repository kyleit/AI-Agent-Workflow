#!/usr/bin/env python3
"""Materialize Blueprint code blocks into validation-only temp files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)[:120] or "block"


def materialize(discovery: dict, root: Path, workflow_id: str) -> list[dict]:
    base = root / ".agents" / "tmp" / "code-block-gate" / workflow_id
    base.mkdir(parents=True, exist_ok=True)
    outputs: list[dict] = []
    for block in discovery.get("blocks", []):
        if not block.get("implementation_ready"):
            continue
        block_dir = base / safe_name(block["id"])
        block_dir.mkdir(parents=True, exist_ok=True)
        target_name = safe_name(Path(block.get("file", "snippet.txt")).name)
        out = block_dir / target_name
        resolved = out.resolve()
        if not str(resolved).startswith(str(base.resolve())):
            outputs.append({"id": block["id"], "status": "BLOCKED", "finding": "materialization escaped temp root"})
            continue
        out.write_text(block.get("code", ""), encoding="utf-8")
        outputs.append({"id": block["id"], "status": "PASS", "path": str(out)})
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--output")
    args = parser.parse_args()
    result = materialize(json.loads(Path(args.discovery).read_text(encoding="utf-8")), Path(args.root), args.workflow_id)
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
