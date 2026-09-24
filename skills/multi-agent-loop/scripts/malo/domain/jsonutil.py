"""Typed JSON helpers (isolate `json.loads` Any at one boundary).

basedpyright strict-full: `json.loads` is `Any`; these helpers cast it to
`object`/typed containers exactly once so callers stay Any-free.
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


def as_object_mapping(value: object) -> Mapping[str, object]:
    """Narrow an object to a typed mapping (empty mapping when not a dict)."""
    if isinstance(value, dict):
        return cast("Mapping[str, object]", value)
    return {}


def as_object_list(value: object) -> list[object]:
    """Narrow an object to a typed list (empty list when not a list)."""
    if isinstance(value, list):
        return cast("list[object]", value)
    return []
