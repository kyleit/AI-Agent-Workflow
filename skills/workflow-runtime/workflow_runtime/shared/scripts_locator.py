"""
workflow_runtime/shared/scripts_locator.py

Utility to find the legacy scripts directory (now internal to the package).
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def find_scripts_dir() -> Path:
    """Return the path to the internal legacy_scripts/ directory."""
    here = Path(__file__).resolve()
    candidate = here.parent.parent / "legacy_scripts"

    if not candidate.exists() or not candidate.is_dir():
        raise FileNotFoundError(f"Missing legacy scripts at {candidate}. Did you run make export?")

    return candidate


def ensure_on_path(scripts_dir: Path | None = None) -> Path:
    """Add scripts_dir to sys.path if not already present. Returns scripts_dir."""
    if scripts_dir is None:
        scripts_dir = find_scripts_dir()
    d = str(scripts_dir)
    if d not in sys.path:
        sys.path.insert(0, d)
    return scripts_dir
