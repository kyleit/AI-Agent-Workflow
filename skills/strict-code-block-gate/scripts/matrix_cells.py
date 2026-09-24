#!/usr/bin/env python3
"""Turn Markdown table text into structured rows.

Every gate rule that used to scan prose reads its structure from here instead.
Keeping the parsing in one module is what makes "read the declaration, never the
prose" enforceable rather than aspirational.

This module must not import any sibling validator. It is the bottom of the
dependency order, and keeping it there is what prevents a cycle between the
coverage rules and the surface rules.
"""

from __future__ import annotations

import re
from pathlib import Path

MATRIX_HEADING = re.compile(
    r"^#{1,6}\s+.*file[- ]by[- ]file change matrix", re.IGNORECASE
)
SCREEN_MATRIX_HEADING = re.compile(
    r"^#{1,6}\s+.*(?:screen\s+and\s+route|route\s+and\s+screen|screen\s+coverage).*?$",
    re.IGNORECASE,
)
SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(?:\|\s*:?-{2,}:?\s*)+\|?\s*$")
ID_RE = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]*")
IGNORE_IDS = {"none", "n/a", "na", "tbd", "todo", "-"}

# A Markdown cell escapes a literal pipe, which is the only way to write a union
# return type inside a table. Splitting on raw pipes shifted every later column,
# and because a shifted value is often a placeholder the row was then reported as
# missing a field it had in fact declared. The sentinel is a control character,
# which cannot occur in a Markdown table, and every cell restores it.
_ESCAPED_PIPE_SENTINEL = "\x00aiwf-escaped-pipe\x00"

# An ignorable whole-cell value. Expressed as a pattern rather than set
# membership because a slash-bearing form can never appear in the identifier
# pattern's output, which left that entry of IGNORE_IDS unreachable.
_IGNORABLE_CELL = re.compile(r"^(?:none|n\s*/\s*a|na|tbd|todo|-{1,3})$", re.IGNORECASE)

# plan-to-blueprint documents that a coverage row may carry an explicit
# not-applicable reason in place of a code-block identifier. The reason is free
# text in any language, so it must never be tokenized.
_NOT_APPLICABLE = re.compile(r"^not[\s_-]*applicable\b", re.IGNORECASE)


def cells(line: str) -> list[str]:
    """Split one table row on unescaped pipes only."""
    value = line.strip().replace("\\|", _ESCAPED_PIPE_SENTINEL)
    if value.startswith("|"):
        value = value[1:]
    if value.endswith("|"):
        value = value[:-1]
    return [
        cell.strip().strip("`").replace(_ESCAPED_PIPE_SENTINEL, "|")
        for cell in value.split("|")
    ]


def header_key(value: str) -> str:
    """Normalize a header for comparison, ignoring punctuation and case."""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def find_column(headers: list[str], *needles: str) -> int | None:
    """Return the index of the first header matching any needle."""
    for index, header in enumerate(headers):
        key = header_key(header)
        if any(needle in key for needle in needles):
            return index
    return None


def normalized_cell(value: str) -> str:
    """Strip surrounding whitespace and code fencing from one cell."""
    return value.strip().strip("`").strip()


def cell_is_not_applicable(value: str) -> bool:
    """Recognize the explicit not-applicable declaration, with or without a reason."""
    return bool(_NOT_APPLICABLE.match(normalized_cell(value)))


def cell_is_ignorable(value: str) -> bool:
    """Recognize a whole-cell placeholder, including forms containing a slash."""
    return bool(_IGNORABLE_CELL.match(normalized_cell(value)))


def ids(value: str) -> list[str]:
    """Extract declared identifiers, or none when the cell declares no identifier."""
    cleaned = normalized_cell(value)
    if not cleaned or cell_is_ignorable(cleaned) or cell_is_not_applicable(cleaned):
        return []
    return [item for item in ID_RE.findall(cleaned) if item.lower() not in IGNORE_IDS]


def integer(value: str) -> int:
    """Read the first whole number in a cell, or zero when it holds none."""
    match = re.search(r"\d+", value or "")
    return int(match.group(0)) if match else 0


def display_path(path: Path | str) -> str:
    """Render a path repository-relative for finding text.

    A finding is read by the document author and copied into reports, so an
    absolute path inside one violates the same path policy the gate enforces.
    """
    text = Path(path).as_posix()
    for marker in ("/docs/", "/skills/", "/contracts/", "/.agents/"):
        index = text.find(marker)
        if index != -1:
            return text[index + 1:]
    return Path(path).name


__all__ = [
    "ID_RE",
    "IGNORE_IDS",
    "MATRIX_HEADING",
    "SCREEN_MATRIX_HEADING",
    "SEPARATOR",
    "cell_is_ignorable",
    "cell_is_not_applicable",
    "cells",
    "display_path",
    "find_column",
    "header_key",
    "ids",
    "integer",
    "normalized_cell",
]
