"""Infrastructure services: system clock and SHA-256 hashing.

Concrete implementations of the `Clock` and `HashService` application ports.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


class SystemClock:
    """UTC wall-clock implementation of the Clock port."""

    def now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Sha256HashService:
    """SHA-256 implementation of the HashService port (AIWF hash algorithm)."""

    def sha256_hex(self, payload: str) -> str:
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
