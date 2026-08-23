#!/usr/bin/env python3
"""Validate gate-visible architecture boundary evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def validate(root: Path, blocks: list[dict]) -> list[dict]:
    contract = root / ".agents" / "contracts" / "engineering-quality-gates.yaml"
    if not contract.exists():
        return [{"status": "BLOCKED", "finding": "missing architecture contract"}]
    results = []
    for block in blocks:
        if not block.get("implementation_ready"):
            continue
        target = block.get("file", "")
        if target.startswith("/") or ":" in Path(target).drive:
            results.append({"id": block["id"], "status": "BLOCKED", "finding": "target path must be repository-relative"})
        else:
            results.append({"id": block["id"], "status": "PASS", "contract": ".agents/contracts/engineering-quality-gates.yaml"})
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--discovery", required=True)
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    data = json.loads(Path(args.discovery).read_text(encoding="utf-8"))
    print(json.dumps(validate(Path(args.root), data.get("blocks", [])), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
