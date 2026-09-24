"""Application ports (interfaces) for dependency injection.

The application layer depends only on these abstractions; concrete file IO,
clock, and hashing live in infrastructure and are injected at composition
time (presentation/cli.py). This keeps the domain and use cases pure and
unit-testable with in-memory fakes.
"""

from __future__ import annotations

from typing import Protocol

from loop_engine.domain.ledger import LedgerEntry
from loop_engine.domain.models import LoopState


class LoopStateRepository(Protocol):
    """Persistence boundary for the single loop-state document per workflow."""

    def load(self, workflow_id: str) -> LoopState | None:
        """Return the stored loop state, or None when no file exists yet."""
        ...

    def save(self, state: LoopState) -> str:
        """Atomically persist the loop state; return the repo-relative path."""
        ...


class LoopLedgerRepository(Protocol):
    """Append-only ledger boundary (one JSONL line per controller cycle)."""

    def append(self, workflow_id: str, entry: LedgerEntry) -> str:
        """Append one entry; return the repo-relative ledger path."""
        ...


class Clock(Protocol):
    """Time boundary. Injected so use cases stay deterministic under test."""

    def now_iso(self) -> str:
        """Return the current UTC time as an ISO-8601 string."""
        ...


class HashService(Protocol):
    """Content hashing boundary (SHA-256), matching the AIWF hash algorithm."""

    def sha256_hex(self, payload: str) -> str:
        """Return the SHA-256 hex digest of the given payload."""
        ...
