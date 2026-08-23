#!/usr/bin/env python3
"""Resolve strict language profiles from a lightweight YAML registry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _list_value(raw: str) -> list[str]:
    raw = raw.strip()
    if not (raw.startswith("[") and raw.endswith("]")):
        return []
    return [item.strip().strip('"').strip("'") for item in raw[1:-1].split(",") if item.strip()]


def load_registry(path: Path) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  ") and not raw.startswith("    ") and raw.strip().endswith(":"):
            current = raw.strip()[:-1].lower()
            profiles[current] = {"key": current}
            continue
        if current and raw.startswith("    ") and ":" in raw:
            key, value = raw.strip().split(":", 1)
            value = value.strip()
            profiles[current][key] = _list_value(value) if value.startswith("[") else value
    return profiles


def resolve(registry: dict[str, dict], language: str, target_file: str) -> dict:
    language_key = (language or "").lower().strip()
    suffix = Path(target_file).suffix.lower()
    filename = Path(target_file).name
    candidates = []
    if language_key in registry:
        candidates.append(registry[language_key])
    for profile in registry.values():
        if suffix and suffix in [ext.lower() for ext in profile.get("extensions", [])]:
            candidates.append(profile)
        if filename and filename in profile.get("filenames", []):
            candidates.append(profile)
    unique = {candidate["profile"]: candidate for candidate in candidates if candidate.get("profile")}
    if not unique:
        return {"status": "BLOCKED", "finding": "missing strict language profile"}
    if len(unique) > 1:
        return {"status": "BLOCKED", "finding": "ambiguous strict language profile", "candidates": sorted(unique)}
    profile = next(iter(unique.values()))
    return {"status": "PASS", "profile": profile.get("profile"), "path": profile.get("path")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", required=True)
    parser.add_argument("--language", required=True)
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    result = resolve(load_registry(Path(args.registry)), args.language, args.file)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
