"""CLI entry for the release engine: `python tools/release.py [options]`."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from . import config as config_mod
from . import engine, versioning


def _repo_root() -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(out.stdout.strip())
    except Exception:
        return Path.cwd()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aiwf-release", description="AIWF release orchestrator")
    p.add_argument("--part", choices=["major", "minor", "patch"], default=None,
                   help="override auto version bump")
    p.add_argument("--dry-run", action="store_true", help="print the plan; no writes/pushes")
    p.add_argument("--plan", action="store_true", help="print computed version + bump only")
    p.add_argument("--config", default=None, help="path to release.config.json")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = _repo_root()
    try:
        cfg = config_mod.load(root if not args.config else Path(args.config).parent)
    except config_mod.ConfigError as e:
        sys.stderr.write(f"[release] config error: {e}\n")
        return 2

    if args.plan:
        plan = versioning.compute_next(root, cfg["version"], args.part)
        print(f"current : {plan['current']}")
        print(f"bump    : {plan['part']}")
        print(f"next    : {plan['next']}")
        return 0

    try:
        receipt = engine.run(root, cfg, args.part, args.dry_run)
    except engine.ReleaseError as e:
        sys.stderr.write(f"\n[release] ABORTED: {e}\n")
        return 1
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"\n[release] ERROR: {e}\n")
        return 1

    tag = f"v{receipt['version']}"
    mode = " (dry-run)" if args.dry_run else ""
    print(f"\n[release] {tag} {receipt['bump_part']}{mode}")
    print(f"  previous : {receipt['previous_version']}")
    print(f"  gates    : {', '.join(g['gate'] for g in receipt['gates'])}")
    for r in receipt["repos"]:
        print(f"  released : {r['path']} -> {r['tag']} ({r['sha'] or 'dry'})")
    print(f"  receipt  : {receipt['receipt_file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
