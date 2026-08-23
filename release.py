#!/usr/bin/env python3
"""AIWF release orchestrator entry point.

Usage:
  python tools/release.py --plan            # show computed next version
  python tools/release.py --dry-run         # full plan, no writes/pushes
  python tools/release.py                    # execute the release
  python tools/release.py --part minor       # override auto bump

Behaviour is driven entirely by release.config.json (see
docs/features/aiwf-release-orchestrator/blueprint.md). The engine lives in the
aiwf_release package next to this file.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from aiwf_release.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
