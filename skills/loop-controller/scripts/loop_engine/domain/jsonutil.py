"""Typed JSON helper (isolate `json.loads` Any at one boundary).

basedpyright strict-full: `json.loads` is `Any`; this casts it to a typed
mapping exactly once so callers stay Any-free.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast


def as_json_object(text: str) -> Mapping[str, object] | None:
    """Parse text; return a typed mapping, or None if it is not a JSON object."""
    parsed = cast(object, json.loads(text))
    if isinstance(parsed, dict):
        return cast("Mapping[str, object]", parsed)
    return None
