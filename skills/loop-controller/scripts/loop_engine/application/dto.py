"""Application-level data transfer objects for the loop use cases."""

from __future__ import annotations

from dataclasses import dataclass

from loop_engine.domain.ledger import LedgerEntry
from loop_engine.domain.models import DecisionResult, LoopState


@dataclass(frozen=True)
class DecideOutput:
    """Result of a decide cycle: the decision, the next state, the ledger row.

    `next_state` and `ledger_entry` are produced without timestamps; the
    persist use case stamps them so decide stays fully deterministic.
    """

    decision: DecisionResult
    next_state: LoopState
    ledger_entry: LedgerEntry


@dataclass(frozen=True)
class PersistInput:
    next_state: LoopState
    ledger_entry: LedgerEntry


@dataclass(frozen=True)
class PersistOutput:
    state_path: str
    ledger_path: str
    state_sha256: str
    updated_at: str
