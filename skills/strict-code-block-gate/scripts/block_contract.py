#!/usr/bin/env python3
"""Single source of truth for the anchored-region modification contract.

A modification to an existing file cannot restate that file's current bytes, so
ADR-202 permits a region declaration for ``operation: modify`` only, and makes it
carry its own proof obligations instead. Four validators must agree on what that
declaration is; keeping the predicate in one module is what stops them drifting
apart the way the gate and the runtime validator already did.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Mapping

MODIFY_OPERATION = "modify"
REGION_SCOPE = "anchored-region"

_ANCHOR_DECLARATION = r"\b(?:class|def|async def|function|const|let|var)\s+{name}\b"


def _normalized_field(value: object) -> str:
    return str(value or "").strip().lower()


def is_region_modify(block: Mapping[str, object]) -> bool:
    """Recognize a declaration that describes a region of an existing file.

    All three conditions are required. Region scope without a modify operation is
    a mistake rather than a shorthand, and the caller rejects it so the author
    learns which of the two fields is wrong.
    """
    return (
        _normalized_field(block.get("operation")) == MODIFY_OPERATION
        and _normalized_field(block.get("block_scope")) == REGION_SCOPE
        and not block.get("full_file")
    )


def normalized_source(path: Path) -> str:
    """Normalize exactly as the existing full-file comparison does.

    A different normalization here would make a correct hash look wrong on a
    checkout with different line endings, which would read as a false accusation
    that the author never opened the file.
    """
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip()


def content_hash(text: str) -> str:
    """Return the hex digest used for a declared ``base_sha256``."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def anchor_present(text: str, anchor: str) -> bool:
    """Apply the anchor rule the runtime SourceContextValidator already applies."""
    name = anchor.rsplit(".", 1)[-1].strip()
    if not name:
        return False
    if name in text:
        return True
    pattern = _ANCHOR_DECLARATION.format(name=re.escape(name))
    return re.search(pattern, text) is not None


__all__ = [
    "MODIFY_OPERATION",
    "REGION_SCOPE",
    "anchor_present",
    "content_hash",
    "is_region_modify",
    "normalized_source",
]
