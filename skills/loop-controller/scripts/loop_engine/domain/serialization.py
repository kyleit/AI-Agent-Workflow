"""Canonical JSON serialization (pure).

A single deterministic serialization used both for writing state files and for
computing their SHA-256 content hash, so the on-disk bytes and the hashed
bytes never diverge.
"""

from __future__ import annotations

import json
from collections.abc import Mapping


def to_canonical_json(data: Mapping[str, object]) -> str:
    """Serialize a mapping to stable, UTF-8-friendly JSON (no BOM, sorted keys)."""
    return json.dumps(
        dict(data),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
