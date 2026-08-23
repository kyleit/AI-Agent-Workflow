"""UlidIdGenerator — monotonic, sortable message ids: <ms_hex>-<counter>-<slug>."""

from __future__ import annotations

import itertools
import time


class UlidIdGenerator:
    def __init__(self) -> None:
        self._counter = itertools.count()

    def next_id(self, sender_slug: str) -> str:
        ms = int(time.time() * 1000)
        n = next(self._counter)
        safe = sender_slug.replace(" ", "-")
        return f"{ms:012x}-{n:04x}-{safe}"
