"""Classify Markdown lines as fence delimiters, fenced code, or prose.

CommonMark lets a fence use more than three backticks so the block can embed a
literal ``` line; the block closes only on a bare fence at least as long as the
opening one. Toggling on every ``` line flips state on such an embedded line and
inverts the prose/code split for the rest of the document. The strict code-block
gate's discover_code_blocks.py applies the same rule, so both agree on what is
code.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator

FENCE = "fence"
CODE = "code"
PROSE = "prose"

_OPENING = re.compile(r"^\s*(`{3,})[^`]*$")
_CLOSING = re.compile(r"^\s*(`{3,})\s*$")


def fence_states(lines: Iterable[str]) -> Iterator[tuple[str, str]]:
    """Yield ``(line, state)`` with state one of FENCE, CODE or PROSE."""
    open_length = 0
    for line in lines:
        if open_length:
            closing = _CLOSING.match(line)
            if closing and len(closing.group(1)) >= open_length:
                open_length = 0
                yield line, FENCE
            else:
                yield line, CODE
            continue
        opening = _OPENING.match(line)
        if opening:
            open_length = len(opening.group(1))
            yield line, FENCE
        else:
            yield line, PROSE
