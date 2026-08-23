#!/usr/bin/env python3
"""Discover implementation-ready fenced code blocks in a Blueprint."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

FENCE_RE = re.compile(r"^```([A-Za-z0-9_+.#-]*)\s*$")
META_RE = re.compile(r"^([A-Za-z_][\w-]*):\s*(.*?)\s*$")
PLACEHOLDER_RE = re.compile(
    r"(^|\n)\s*(TODO|FIXME|TBD)\b|\.{3,}|<\s*(implementation|code|todo)[^>]*>",
    re.IGNORECASE,
)


def _metadata(lines: list[str], fence_index: int) -> dict[str, str]:
    meta: dict[str, str] = {}
    idx = fence_index - 1
    while idx >= 0:
        line = lines[idx].strip()
        if not line:
            idx -= 1
            continue
        match = META_RE.match(line)
        if not match:
            break
        meta[match.group(1).replace("-", "_").lower()] = match.group(2).strip()
        idx -= 1
    return meta


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "yes", "1", "y"}


def discover(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    blocks: list[dict] = []
    findings: list[str] = []
    i = 0
    while i < len(lines):
        match = FENCE_RE.match(lines[i])
        if not match:
            i += 1
            continue
        fence_language = match.group(1).strip()
        start = i + 1
        code_lines: list[str] = []
        i += 1
        while i < len(lines) and not lines[i].startswith("```"):
            code_lines.append(lines[i])
            i += 1
        end = i + 1 if i < len(lines) else len(lines)
        code = "\n".join(code_lines).rstrip() + "\n"
        meta = _metadata(lines, start - 1)
        implementation_ready = _truthy(meta.get("implementation_ready"))
        language = meta.get("language") or fence_language
        block_id = meta.get("id") or f"block-{len(blocks) + 1}"
        block_hash = hashlib.sha256(
            "|".join(
                [
                    block_id,
                    language,
                    meta.get("file", ""),
                    meta.get("operation", ""),
                    meta.get("symbol", ""),
                    code,
                ]
            ).encode("utf-8")
        ).hexdigest()
        block = {
            "id": block_id,
            "language": language,
            "file": meta.get("file", ""),
            "operation": meta.get("operation", ""),
            "symbol": meta.get("symbol", ""),
            "implementation_ready": implementation_ready,
            "start_line": start + 1,
            "end_line": end,
            "sha256": block_hash,
            "code": code,
            "status": "PASS",
            "findings": [],
        }
        if implementation_ready:
            for field in ("id", "language", "file", "operation"):
                if not meta.get(field):
                    block["status"] = "BLOCKED"
                    block["findings"].append(f"missing metadata field: {field}")
            if PLACEHOLDER_RE.search(code):
                block["status"] = "FAIL"
                block["findings"].append("placeholder or incomplete code detected")
        else:
            block["status"] = "NOT_APPLICABLE"
        blocks.append(block)
        i += 1
    return {"blueprint": str(path), "blocks": blocks, "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--blueprint", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = discover(Path(args.blueprint))
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
